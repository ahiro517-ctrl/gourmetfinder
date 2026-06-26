"""Google スプレッドシート入出力。

タブ構成:
  「候補」    : 提案を毎週追記。人間がここに ○/△/× などを記入する。
  「_features」: 各候補の特徴量(JSON)。学習に使う内部データ。
  「_state」   : 既出 place_id・学習済み place_id などの内部状態。
（_ で始まるタブは内部用。基本さわらないでOK）
"""

from __future__ import annotations

import json
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

CANDIDATES_SHEET = "候補"
FEATURES_SHEET = "_features"
STATE_SHEET = "_state"

CANDIDATE_HEADERS = [
    "実行日",
    "place_id",
    "店名",
    "住所",
    "業種",
    "スコア",
    "取材理由",
    "評価",      # 人間が記入: ○ / △ / ×
    "タグ",      # 人間が記入: 例 チェーン嫌, 遠い, ジャンル違い, 良い
    "コメント",  # 人間が記入: 自由記述
    "ステータス",  # 人間が記入: 未 / 取材済
]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsClient:
    def __init__(self, service_account_json: str, spreadsheet_id: str):
        if not service_account_json:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_JSON が設定されていません。")
        if not spreadsheet_id:
            raise ValueError("GOURMET_SPREADSHEET_ID が設定されていません。")
        info = json.loads(service_account_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        self.gc = gspread.authorize(creds)
        self.sh = self.gc.open_by_key(spreadsheet_id)
        self._ensure_sheets()

    def _ensure_sheets(self) -> None:
        existing = {ws.title for ws in self.sh.worksheets()}
        if CANDIDATES_SHEET not in existing:
            ws = self.sh.add_worksheet(CANDIDATES_SHEET, rows=1000, cols=len(CANDIDATE_HEADERS))
            ws.append_row(CANDIDATE_HEADERS, value_input_option="USER_ENTERED")
        if FEATURES_SHEET not in existing:
            ws = self.sh.add_worksheet(FEATURES_SHEET, rows=2000, cols=2)
            ws.append_row(["place_id", "features_json"])
        if STATE_SHEET not in existing:
            ws = self.sh.add_worksheet(STATE_SHEET, rows=100, cols=2)
            ws.append_row(["key", "value"])

    # ---- 候補 -------------------------------------------------------
    def read_candidates(self) -> list[dict[str, Any]]:
        ws = self.sh.worksheet(CANDIDATES_SHEET)
        return ws.get_all_records()

    def append_candidates(self, rows: list[list[Any]]) -> None:
        if not rows:
            return
        ws = self.sh.worksheet(CANDIDATES_SHEET)
        ws.append_rows(rows, value_input_option="USER_ENTERED")

    # ---- 特徴量 -----------------------------------------------------
    def read_features(self) -> dict[str, dict[str, float]]:
        ws = self.sh.worksheet(FEATURES_SHEET)
        out: dict[str, dict[str, float]] = {}
        for row in ws.get_all_records():
            pid = str(row.get("place_id", ""))
            raw = row.get("features_json", "")
            if pid and raw:
                try:
                    out[pid] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    continue
        return out

    def append_features(self, mapping: dict[str, dict[str, float]]) -> None:
        if not mapping:
            return
        ws = self.sh.worksheet(FEATURES_SHEET)
        rows = [[pid, json.dumps(feat, ensure_ascii=False)] for pid, feat in mapping.items()]
        ws.append_rows(rows, value_input_option="RAW")

    # ---- 状態 -------------------------------------------------------
    def get_state(self, key: str, default: Any = None) -> Any:
        ws = self.sh.worksheet(STATE_SHEET)
        for row in ws.get_all_records():
            if str(row.get("key", "")) == key:
                raw = row.get("value", "")
                try:
                    return json.loads(raw) if raw else default
                except (json.JSONDecodeError, TypeError):
                    return default
        return default

    def set_state(self, key: str, value: Any) -> None:
        ws = self.sh.worksheet(STATE_SHEET)
        records = ws.get_all_records()
        payload = json.dumps(value, ensure_ascii=False)
        for i, row in enumerate(records, start=2):  # 1行目はヘッダ
            if str(row.get("key", "")) == key:
                ws.update_cell(i, 2, payload)
                return
        ws.append_row([key, payload], value_input_option="RAW")
