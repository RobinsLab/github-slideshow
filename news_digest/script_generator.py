import anthropic
from .fetcher import Article
from . import config
from datetime import datetime, timedelta, timezone


def generate_news_script(articles: list[Article]) -> str:
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY が設定されていません")

    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst).strftime("%Y年%m月%d日")

    article_details = "\n\n".join(
        f"【記事{i+1}】\n出典: {a.source} ({a.category})\nタイトル: {a.title}\n概要: {a.summary}\nURL: {a.link}"
        for i, a in enumerate(articles)
    )

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""あなたはプロのニュースキャスターです。
以下の記事を基に、ニュース番組の読み上げ原稿を作成してください。

日付: {today}

要件:
1. 番組オープニング（挨拶と今日のトピック概要）
2. 各記事のニュース読み上げ（自然な導入→本題→解説・影響）
3. 記事間のつなぎの言葉（自然な遷移）
4. 番組エンディング（まとめと締めの挨拶）

スタイル:
- NHKニュースのような落ち着いたトーン
- 1記事あたり150〜250文字程度
- 専門用語は簡潔に補足
- WSJの英語記事は日本語に翻訳して読み上げ
- 読み上げに適した自然な日本語（句読点を適切に配置）

記事:
{article_details}

原稿のみを出力してください。メタ情報や注釈は不要です。"""
        }]
    )

    return response.content[0].text
