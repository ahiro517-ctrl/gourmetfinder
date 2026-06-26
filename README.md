# gourmetfinder — 品川・港南エリア 取材候補ソーシング

品川駅・港南エリアの飲食店から「取材したい候補」を、**理由付き**で毎週自動提案するツールです。
新店オープンの検知や、旬でなくても料理がおいしい・独自性のある店を拾い、全国チェーンは優先度を下げます。
人間が ○/△/× の簡単なフィードバックを返すと、次回以降のおすすめ順位に反映されます。

## 対象エリア
- 港区港南（品川駅 港南口側）
- 品川区 北品川 1〜2丁目 / 東品川 1丁目

## どう動くか
```
週1回(GitHub Actions) → Google Places で店舗取得 → 新店検知＋スコアリング
                      → スプレッドシートに提案 → 人が○×記入 → 次回学習に反映
```

## ドキュメント
- 📖 **[セットアップ手順（非エンジニア向け）](docs/SETUP_GUIDE.md)** ← まずはこちら
- 📋 [仕様書](docs/SPEC.md)

## ざっくり構成
| 場所 | 役割 |
|---|---|
| `config/` | 人が編集する設定（エリア・重み・チェーン語） |
| `gourmetfinder/` | プログラム本体 |
| `.github/workflows/weekly.yml` | 週次自動実行 |
| `fixtures/` | 動作確認用サンプルデータ |
| `tests/` | テスト |

## 動作確認（API不要）
```bash
pip install -r requirements.txt
python -m gourmetfinder --dry-run   # サンプルデータでスコア順に候補表示
pytest -q                            # テスト
```

## 必要な GitHub Secrets
| 名前 | 中身 |
|---|---|
| `GOOGLE_PLACES_API_KEY` | Google Places APIキー |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | サービスアカウントのJSON（全文） |
| `GOURMET_SPREADSHEET_ID` | 提案を書き込むスプレッドシートのID |

詳細は [セットアップ手順](docs/SETUP_GUIDE.md) を参照。
