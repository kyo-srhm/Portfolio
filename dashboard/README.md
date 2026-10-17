# 統合ダッシュボード（Media & EA Dashboard）

note、X、WordPress（GA4）、MQL5 Market の実績を一か所に集めて、スマートフォンから見られるようにするプロジェクトです。
設計のたたき台は [docs/design-v1.0.txt](docs/design-v1.0.txt) です。

## 役割分担

| 部分 | 技術 | 置き場所 | 状態 |
|---|---|---|---|
| GA4 からの日別データ取得 | Python | [python/](python/) | 初版あり |
| データ保存・REST API・画面 | WordPress プラグイン（PHP / JavaScript / Chart.js） | `plugin/`（予定） | 未着手 |
| 定期実行 | エックスサーバーの Cron | サーバーパネル | 未設定 |

設計書では GA4 の取得も PHP で行う前提ですが、ここでは **取得を Python、保存と表示を WordPress** に分けています。
Python スクリプトはエックスサーバー上で Cron から動かし、取得した値をプラグインの `POST /wp-json/med/v1/snapshot` に送ります。
認証は WordPress のアプリケーションパスワード（HTTPS 必須）を使います。

```
エックスサーバー Cron ──▶ python -m med_sync ──▶ GA4 Data API
                                │
                                └─ POST /wp-json/med/v1/snapshot ──▶ WordPress プラグイン ──▶ DB / 画面
```

## Python スクリプトの使い方

```bash
cd dashboard/python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # 値を書き換える（.env はコミットされない）
set -a && source .env && set +a

python -m pytest -q           # テスト
python -m med_sync --dry-run  # GA4 から取得して表示だけする
python -m med_sync            # WordPress に登録する
```

エックスサーバーの Cron 例（1日1回、朝6時）:

```
0 6 * * * cd $HOME/portfolio/dashboard/python && set -a && . ./.env && set +a && .venv/bin/python -m med_sync >> $HOME/logs/med_sync.log 2>&1
```

## 秘密情報の扱い

- GA4 のサービスアカウント鍵（JSON）とアプリケーションパスワードはリポジトリに入れません。`.gitignore` で除外しています。
- 鍵はエックスサーバーの `public_html` の外に置き、パーミッションを 600 にします。
