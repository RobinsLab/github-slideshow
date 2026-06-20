#!/usr/bin/env python3
"""
ニュースダイジェスト - モバイル対応Webアプリ

起動:
  python -m news_digest.web
  python -m news_digest.web --port 8080
  python -m news_digest.web --from-file test_articles.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))

_articles_cache: list = []
_from_file: str | None = None


def _get_articles() -> list:
    global _articles_cache
    if _articles_cache:
        return _articles_cache

    if _from_file:
        from .fetcher import Article
        with open(_from_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        _articles_cache = []
        for i, item in enumerate(data, 1):
            _articles_cache.append(Article(
                id=i,
                title=item["title"],
                summary=item.get("summary", ""),
                link=item.get("link", ""),
                source=item.get("source", "Unknown"),
                category=item.get("category", ""),
                published=item.get("published", ""),
            ))
        return _articles_cache

    from .fetcher import fetch_all_articles
    _articles_cache = fetch_all_articles()

    if not _articles_cache:
        try:
            from .web_fetcher import fetch_all_from_newsapi
            _articles_cache = fetch_all_from_newsapi()
        except Exception:
            pass

    return _articles_cache


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/articles')
def api_articles():
    try:
        articles = _get_articles()
        from . import config

        if config.ANTHROPIC_API_KEY:
            from .recommender import recommend_articles
            recommended = recommend_articles(articles, top_n=15)
        else:
            recommended = articles[:15]

        return jsonify({
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "summary": a.summary,
                    "link": a.link,
                    "source": a.source,
                    "category": a.category,
                    "published": a.published,
                }
                for a in recommended
            ]
        })
    except Exception as e:
        return jsonify({"articles": [], "error": str(e)})


@app.route('/api/generate-script', methods=['POST'])
def api_generate_script():
    try:
        data = request.get_json()
        article_ids = set(data.get("article_ids", []))

        all_articles = _get_articles()
        selected = [a for a in all_articles if a.id in article_ids]

        if not selected:
            return jsonify({"error": "記事が選択されていません"})

        from . import config
        if not config.ANTHROPIC_API_KEY:
            return jsonify({"error": "ANTHROPIC_API_KEY が設定されていません"})

        from .script_generator import generate_news_script
        script = generate_news_script(selected)
        return jsonify({"script": script})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/generate-audio', methods=['POST'])
def api_generate_audio():
    try:
        data = request.get_json()
        script = data.get("script", "")

        if not script:
            return jsonify({"error": "原稿が空です"})

        from .audio_generator import generate_audio
        result_path = generate_audio(script)
        filename = os.path.basename(result_path)

        return jsonify({
            "audio_url": f"/output/{filename}",
            "filename": filename,
        })
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/output/<path:filename>')
def serve_output(filename):
    from . import config
    output_dir = os.path.abspath(config.OUTPUT_DIR)
    return send_from_directory(output_dir, filename)


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    global _articles_cache
    _articles_cache = []
    return jsonify({"status": "ok"})


def main():
    global _from_file

    parser = argparse.ArgumentParser(description="ニュースダイジェスト Webアプリ")
    parser.add_argument("--port", type=int, default=5000, help="ポート番号 (default: 5000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="ホスト (default: 0.0.0.0)")
    parser.add_argument("--from-file", type=str, default=None, help="JSONファイルから記事を読み込み")
    args = parser.parse_args()

    _from_file = args.from_file

    from . import config
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    print(f"🌐 ニュースダイジェスト Web アプリ起動中...")
    print(f"📱 スマホからアクセス: http://<your-ip>:{args.port}")
    print(f"💻 ローカル: http://localhost:{args.port}")

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
