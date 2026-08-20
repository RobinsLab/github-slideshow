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

## Android (Termux) で動かす

Puma (`nio4r`) はネイティブ拡張のビルドが必要で、Termux では失敗することが
あります。その場合は Puma を外して WEBrick(純Ruby実装)で起動してください。

```bash
pkg update && pkg upgrade
pkg install ruby git clang make

git clone https://github.com/RobinsLab/github-slideshow.git
cd github-slideshow/health-tracker

# まずは普通にインストールを試す
bundle install

# もし puma/nio4r のビルドで失敗したら、puma を外して入れ直す
bundle config set --local without puma_server
bundle install

export ANTHROPIC_API_KEY=sk-ant-...
bundle exec rackup -s webrick -p 4567 -o 127.0.0.1
```

同じ端末のブラウザで http://localhost:4567 を開けば操作できます。写真での
食事記録は、フォームのファイル選択でカメラを直接起動して撮影できます。

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
