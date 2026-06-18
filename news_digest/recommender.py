import anthropic
from .fetcher import Article
from . import config


def recommend_articles(articles: list[Article], top_n: int = 10) -> list[Article]:
    if not config.ANTHROPIC_API_KEY:
        print("⚠️  ANTHROPIC_API_KEY未設定のため、新着順で上位記事を返します")
        return articles[:top_n]

    article_text = "\n".join(
        f"ID:{a.id} | {a.source}/{a.category} | {a.title} | {a.summary[:100]}"
        for a in articles
    )

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""あなたはビジネスパーソン向けニュースキュレーターです。
以下の記事リストから、最も重要で読むべき記事を{top_n}件選んでください。

選定基準:
- マーケットや経済への影響度
- テクノロジー・ビジネストレンドとしての重要性
- 日本と世界の両方の視点をバランスよくカバー
- 速報性・話題性

出力形式: 選んだ記事のIDをカンマ区切りで出力してください。IDのみを出力し、説明は不要です。
例: 3,7,12,1,15,8,22,4,19,11

記事リスト:
{article_text}"""
        }]
    )

    try:
        ids_text = response.content[0].text.strip()
        selected_ids = [int(x.strip()) for x in ids_text.split(",") if x.strip().isdigit()]
        id_to_article = {a.id: a for a in articles}
        recommended = [id_to_article[aid] for aid in selected_ids if aid in id_to_article]
        return recommended[:top_n] if recommended else articles[:top_n]
    except Exception:
        return articles[:top_n]
