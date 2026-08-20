# 食事・体重トラッカー (health-tracker)

健康促進・ダイエットを目的とした、食事と体重の記録アプリです。毎日の記録を Claude
(Anthropic API) で分析し、1日の終わりにサマリレポートを生成します。

## 機能

- **食事記録**: 朝・昼・晩の3回、写真またはテキストで記録。Claude が品目・カロリー・
  栄養バランスを推定し、その食事に対する改善提案を返します。記録すると当日ここまでの
  合計カロリー・栄養バランスも表示されます。記録は蓄積され、傾向の確認に使えます。
- **体重記録**: 朝(食前)・夜(就寝前)の2回、テキストで記録します。
- **サマリレポート**: その日の食事・体重のサマリ、辛口総合評価、過去1週間の推移、
  週間の辛口総合評価、改善提案を Claude が生成します(`/report` または
  `bin/generate_report.rb`)。

## セットアップ

```bash
cd health-tracker
bundle install
export ANTHROPIC_API_KEY=sk-ant-...   # 未設定の場合は `ant auth login` でも可
bundle exec rackup -p 4567
```

ブラウザで http://localhost:4567 を開いてください。

モデルは既定で `claude-opus-5` を使用します。変更したい場合は `ANTHROPIC_MODEL`
環境変数を設定してください。

## 1日の終わりのレポート自動生成

```bash
bundle exec ruby bin/generate_report.rb        # 今日分
bundle exec ruby bin/generate_report.rb 2026-08-20  # 日付指定
```

cron などで1日1回(例: 23:00)実行すると、`data/reports/YYYY-MM-DD.md` に
レポートが保存されます。

## データの保存

DB は使わず、日付ごとの JSON ファイルに記録を保存します(`data/meals/`,
`data/weights/`, `data/reports/`)。個人の記録データは `.gitignore` で除外して
います。
