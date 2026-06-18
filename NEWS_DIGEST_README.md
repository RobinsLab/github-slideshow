# 📻 ニュースダイジェスト音声生成ツール

日経新聞・WSJから毎朝ニュースを取得し、AIがおすすめ記事を選定。
選択した記事からニュース番組風の原稿を自動生成し、音声データ（MP3）に変換します。

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env に ANTHROPIC_API_KEY を設定
```

## 使い方

### 対話モード（記事を選んで音声化）
```bash
python -m news_digest.main
```

### 自動モード（上位N件で自動生成）
```bash
python -m news_digest.main --auto --top 5
```

### 記事一覧のみ表示
```bash
python -m news_digest.main --list-only
```

### 原稿のみ生成（音声なし）
```bash
python -m news_digest.main --auto --script-only
```

### NewsAPIを使用（RSS不可時のフォールバック）
```bash
# .env に NEWSAPI_KEY を設定
python -m news_digest.main --source newsapi
```

## GitHub Actions 自動実行

毎朝6:30 (JST) に自動でニュースダイジェストを生成します。

### 必要なSecret設定
1. リポジトリの Settings → Secrets and variables → Actions
2. `ANTHROPIC_API_KEY` を追加

生成された音声はArtifactとして7日間保存されます。
手動実行も Actions タブから可能です。

## アーキテクチャ

```
news_digest/
├── config.py           # 設定（RSS URL、TTS音声、出力先）
├── fetcher.py          # RSS フィード取得・パース
├── web_fetcher.py      # NewsAPI フォールバック
├── recommender.py      # Claude AI による記事レコメンド
├── script_generator.py # ニュース番組風原稿の自動生成
├── audio_generator.py  # TTS 音声変換（edge-tts / gTTS）
└── main.py             # CLI エントリーポイント
```

## 必要な環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | ✅ | Claude API キー（レコメンド・原稿生成） |
| `NEWSAPI_KEY` | - | NewsAPI キー（RSSフォールバック時） |
| `TTS_VOICE_JA` | - | 日本語TTS音声 (default: `ja-JP-NanamiNeural`) |
| `TTS_VOICE_EN` | - | 英語TTS音声 (default: `en-US-JennyNeural`) |
| `OUTPUT_DIR` | - | 出力先ディレクトリ (default: `./output`) |

## TTS音声オプション

### 日本語
- `ja-JP-NanamiNeural` (女性、デフォルト)
- `ja-JP-KeitaNeural` (男性)

### 英語
- `en-US-JennyNeural` (女性、デフォルト)
- `en-US-GuyNeural` (男性)
