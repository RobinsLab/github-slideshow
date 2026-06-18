import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TTS_VOICE_JA = os.getenv("TTS_VOICE_JA", "ja-JP-NanamiNeural")
TTS_VOICE_EN = os.getenv("TTS_VOICE_EN", "en-US-JennyNeural")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")

NIKKEI_RSS_FEEDS = {
    "トップ": "https://assets.wor.jp/rss/rdf/nikkei/news.rdf",
    "経済": "https://assets.wor.jp/rss/rdf/nikkei/keizai.rdf",
    "国際": "https://assets.wor.jp/rss/rdf/nikkei/kokusai.rdf",
    "企業": "https://assets.wor.jp/rss/rdf/nikkei/kigyou.rdf",
    "テクノロジー": "https://assets.wor.jp/rss/rdf/nikkei/it.rdf",
    "マーケット": "https://assets.wor.jp/rss/rdf/nikkei/market.rdf",
}

WSJ_RSS_FEEDS = {
    "World": "https://feeds.a.wsj.com/rss/RSSWorldNews.xml",
    "Markets": "https://feeds.a.wsj.com/rss/RSSMarketsMain.xml",
    "Technology": "https://feeds.a.wsj.com/rss/RSSTECH.xml",
    "Business": "https://feeds.a.wsj.com/rss/RSSBusiness.xml",
}
