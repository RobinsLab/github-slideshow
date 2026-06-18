"""
WebSearch/API経由でのニュース取得（RSS取得が使えない環境向け）

このモジュールはNewsAPI (https://newsapi.org) を使用します。
無料プランで1日100リクエストまで利用可能。

環境変数:
  NEWSAPI_KEY: NewsAPIのAPIキー
"""

import json
import urllib.request
import os
from datetime import datetime, timedelta, timezone
from .fetcher import Article


NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")


def fetch_from_newsapi(query: str, language: str = "ja", page_size: int = 20) -> list[Article]:
    if not NEWSAPI_KEY:
        print("⚠️  NEWSAPI_KEY が未設定です")
        return []

    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst)
    from_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")

    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={query}&language={language}&from={from_date}"
        f"&sortBy=publishedAt&pageSize={page_size}"
        f"&apiKey={NEWSAPI_KEY}"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NewsDigestBot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        articles = []
        for item in data.get("articles", []):
            pub = item.get("publishedAt", "")
            if pub:
                try:
                    dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                    pub = dt.astimezone(jst).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

            articles.append(Article(
                title=item.get("title", ""),
                summary=item.get("description", "") or "",
                link=item.get("url", ""),
                source=item.get("source", {}).get("name", "Unknown"),
                category=query,
                published=pub,
            ))
        return articles
    except Exception as e:
        print(f"  [WARN] NewsAPI取得失敗: {e}")
        return []


def fetch_all_from_newsapi() -> list[Article]:
    queries_ja = ["経済", "テクノロジー", "株式市場"]
    queries_en = ["economy", "technology", "markets"]

    all_articles = []

    for q in queries_ja:
        print(f"📰 NewsAPI取得中: {q}...")
        articles = fetch_from_newsapi(q, language="ja", page_size=10)
        all_articles.extend(articles)
        print(f"  → {len(articles)}件")

    for q in queries_en:
        print(f"📰 NewsAPI取得中: {q}...")
        articles = fetch_from_newsapi(q, language="en", page_size=10)
        all_articles.extend(articles)
        print(f"  → {len(articles)}件")

    for i, article in enumerate(all_articles, 1):
        article.id = i

    return all_articles
