"""週次パイプライン本体。取得 → 学習 → スコアリング → 出力 をまとめる。"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import config as cfgmod
from . import scoring
from .blocklist import is_blocked
from .chains import is_chain
from .geo import point_in_polygon
from .learning import DISLIKE, Feedback, learn_chain_keywords, update_weights
from .models import Candidate, Place
from .reasons import build_reasons, summary_line


def _today() -> str:
    return dt.date.today().isoformat()


def filter_to_area(places: list[Place], polygon: list[list[float]]) -> list[Place]:
    return [p for p in places if point_in_polygon(p.lat, p.lng, polygon)]


def _excluded_and_proposed(candidate_rows: list[dict]) -> tuple[set[str], set[str]]:
    """既出 place_id と、除外(却下/取材済) place_id を返す。"""
    proposed: set[str] = set()
    excluded: set[str] = set()
    for row in candidate_rows:
        pid = str(row.get("place_id", ""))
        if not pid:
            continue
        proposed.add(pid)
        if str(row.get("評価", "")).strip() in DISLIKE:
            excluded.add(pid)
        if str(row.get("ステータス", "")).strip() == "取材済":
            excluded.add(pid)
    return proposed, excluded


def _collect_feedback(
    candidate_rows: list[dict],
    features_map: dict[str, dict[str, float]],
    learned_ids: set[str],
) -> list[Feedback]:
    feedback: list[Feedback] = []
    for row in candidate_rows:
        pid = str(row.get("place_id", ""))
        evaluation = str(row.get("評価", "")).strip()
        if not pid or not evaluation or pid in learned_ids:
            continue
        feedback.append(
            Feedback(
                place_id=pid,
                evaluation=evaluation,
                tags=str(row.get("タグ", "")),
                features=features_map.get(pid, {}),
            )
        )
    return feedback


def build_candidates(
    places: list[Place],
    settings: cfgmod.Settings,
    *,
    seen_ids: set[str],
    skip_ids: set[str],
    first_run: bool,
    nationwide_counter=None,
) -> list[Candidate]:
    cands_cfg = settings.config.get("candidates", {})
    weights = settings.weight_values
    keywords = settings.chain_keywords
    block_keywords = settings.block_keywords
    nationwide_threshold = settings.chains.get("nationwide_threshold", 8)

    out: list[Candidate] = []
    for p in places:
        if p.place_id in skip_ids:
            continue
        if (p.business_status or "OPERATIONAL") != "OPERATIONAL":
            continue
        # 取材NG（運営会社・店舗）はスコアに関係なく完全除外
        if is_blocked(p, block_keywords):
            continue

        # 初回は基準作成のみ（全件を「新店」にしない）
        is_new = (
            (not first_run)
            and p.place_id not in seen_ids
            and p.review_count <= cands_cfg.get("new_store_max_reviews", 15)
        )
        chain = is_chain(
            p,
            keywords,
            nationwide_count_fn=nationwide_counter,
            nationwide_threshold=nationwide_threshold,
        )
        features = scoring.extract_features(
            p,
            is_new=is_new,
            is_chain=chain,
            min_rating_reviews=cands_cfg.get("min_rating_reviews", 5),
            hidden_gem_max_reviews=cands_cfg.get("hidden_gem_max_reviews", 40),
        )
        cand = scoring.build_candidate(
            p, features, weights, is_new=is_new, is_chain=chain
        )
        cand.reasons = build_reasons(cand)
        out.append(cand)

    out.sort(key=lambda c: c.score, reverse=True)
    return out


def _candidate_to_row(cand: Candidate) -> list:
    p = cand.place
    return [
        _today(),
        p.place_id,
        p.name,
        p.address,
        p.primary_type or (p.types[0] if p.types else ""),
        round(cand.score, 3),
        summary_line(cand),
        "",  # 評価（人間記入）
        "",  # タグ
        "",  # コメント
        "未",  # ステータス
    ]


# =====================================================================
# 本番実行（スプレッドシート連携あり）
# =====================================================================
def run(settings: cfgmod.Settings) -> dict:
    from .places import PlacesClient, make_nationwide_counter
    from .sheets import SheetsClient

    places_cfg = settings.config.get("places", {})
    area = settings.config.get("area", {})

    client = PlacesClient(
        settings.places_api_key,
        language=places_cfg.get("language", "ja"),
        region=places_cfg.get("region", "JP"),
    )
    raw_places = client.search_all_circles(
        area.get("search_circles", []), places_cfg.get("included_types", [])
    )
    places = filter_to_area(raw_places, area.get("polygon", []))

    sheets = SheetsClient(settings.service_account_json, settings.spreadsheet_id)
    candidate_rows = sheets.read_candidates()
    features_map = sheets.read_features()
    seen_ids = set(sheets.get_state("seen_place_ids", []) or [])
    learned_ids = set(sheets.get_state("learned_place_ids", []) or [])
    first_run = len(seen_ids) == 0

    # --- 学習（前回までのフィードバックを反映）-----------------------
    feedback = _collect_feedback(candidate_rows, features_map, learned_ids)
    if feedback:
        new_weights = update_weights(
            settings.weight_values,
            feedback,
            learning_rate=settings.weights.get("learning_rate", 0.3),
            bounds=settings.weights.get("bounds", {}),
        )
        settings.weights["weights"] = new_weights
        cfgmod.save_weights(settings.weights)

        name_by_id = {
            str(r.get("place_id", "")): str(r.get("店名", "")) for r in candidate_rows
        }
        new_keywords = learn_chain_keywords(
            settings.chain_keywords, feedback, name_by_place_id=name_by_id
        )
        if new_keywords != settings.chain_keywords:
            settings.chains["keywords"] = new_keywords
            cfgmod.save_chains(settings.chains)

        learned_ids |= {fb.place_id for fb in feedback}
        sheets.set_state("learned_place_ids", sorted(learned_ids))

    # --- 候補生成 ----------------------------------------------------
    proposed, excluded = _excluded_and_proposed(candidate_rows)
    skip_ids = proposed | excluded
    counter = make_nationwide_counter(
        client, places_cfg.get("enable_nationwide_chain_check", False)
    )
    candidates = build_candidates(
        places,
        settings,
        seen_ids=seen_ids,
        skip_ids=skip_ids,
        first_run=first_run,
        nationwide_counter=counter,
    )

    per_run = settings.config.get("candidates", {}).get("per_run", 12)
    top = candidates[:per_run]

    # --- 出力 --------------------------------------------------------
    sheets.append_candidates([_candidate_to_row(c) for c in top])
    sheets.append_features({c.place.place_id: c.features for c in top})

    # 既出 place_id を更新（次回の新店検知の基準）
    seen_ids |= {p.place_id for p in places}
    sheets.set_state("seen_place_ids", sorted(seen_ids))

    return {
        "fetched": len(raw_places),
        "in_area": len(places),
        "proposed": len(top),
        "first_run": first_run,
        "feedback_learned": len(feedback),
    }


# =====================================================================
# ドライラン（API・シート不要。fixtures で動作確認）
# =====================================================================
def run_dry(settings: cfgmod.Settings, fixture: Path, out_csv: Path) -> dict:
    import csv

    data = json.loads(Path(fixture).read_text(encoding="utf-8"))
    places = [Place.from_places_api(p) for p in data]
    area = settings.config.get("area", {})
    in_area = filter_to_area(places, area.get("polygon", []))

    candidates = build_candidates(
        in_area,
        settings,
        seen_ids=set(),  # 既出なし＝今回はみな初出
        skip_ids=set(),
        first_run=False,  # ドライランでは新店判定も見たいので False
    )
    per_run = settings.config.get("candidates", {}).get("per_run", 12)
    top = candidates[:per_run]

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        from .sheets import CANDIDATE_HEADERS

        w.writerow(CANDIDATE_HEADERS)
        for c in top:
            w.writerow(_candidate_to_row(c))

    print(f"取得 {len(places)}件 / エリア内 {len(in_area)}件 / 提案 {len(top)}件")
    print("-" * 60)
    for i, c in enumerate(top, 1):
        print(f"{i:2}. [{c.score:5.2f}] {c.place.name}")
        print(f"      {summary_line(c)}")
    print("-" * 60)
    print(f"CSV出力: {out_csv}")

    return {"in_area": len(in_area), "proposed": len(top)}
