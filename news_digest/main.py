#!/usr/bin/env python3
"""
ニュースダイジェスト音声生成ツール

使い方:
  # 対話モード: 記事を取得→レコメンド→選択→音声生成
  python -m news_digest.main

  # 自動モード: レコメンド上位N件で自動生成
  python -m news_digest.main --auto --top 5

  # 記事取得のみ（一覧表示）
  python -m news_digest.main --list-only

  # NewsAPIをソースに使用
  python -m news_digest.main --source newsapi

  # 原稿のみ生成（音声なし）
  python -m news_digest.main --auto --script-only
"""

import argparse
import json
import sys
from .fetcher import fetch_all_articles, Article
from .recommender import recommend_articles
from .script_generator import generate_news_script
from .audio_generator import generate_audio


def _load_from_file(path: str) -> list[Article]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    articles = []
    for i, item in enumerate(data, 1):
        articles.append(Article(
            id=i,
            title=item["title"],
            summary=item.get("summary", ""),
            link=item.get("link", ""),
            source=item.get("source", "Unknown"),
            category=item.get("category", ""),
            published=item.get("published", ""),
        ))
    return articles


def _fetch_articles(source: str, from_file: str | None = None) -> list[Article]:
    if from_file:
        print(f"📂 ファイルから記事を読み込み: {from_file}")
        return _load_from_file(from_file)
    if source == "newsapi":
        from .web_fetcher import fetch_all_from_newsapi
        return fetch_all_from_newsapi()
    else:
        articles = fetch_all_articles()
        if not articles:
            print("⚠️  RSS取得失敗。NewsAPIにフォールバック...")
            from .web_fetcher import fetch_all_from_newsapi
            return fetch_all_from_newsapi()
        return articles


def parse_selection(input_str: str, max_id: int) -> list[int]:
    selected = []
    for part in input_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                selected.extend(range(int(start), int(end) + 1))
            except ValueError:
                continue
        elif part.isdigit():
            selected.append(int(part))
    return [s for s in selected if 1 <= s <= max_id]


def interactive_mode(source: str, script_only: bool = False, from_file: str | None = None):
    print("=" * 60)
    print("📻 ニュースダイジェスト音声生成ツール")
    print("=" * 60)
    print()

    articles = _fetch_articles(source, from_file)
    if not articles:
        print("❌ 記事が取得できませんでした")
        sys.exit(1)

    print(f"\n合計 {len(articles)} 件の記事を取得しました")
    print("\n🤖 AIがおすすめ記事を選定中...\n")

    recommended = recommend_articles(articles)

    print("=" * 60)
    print("📋 おすすめ記事一覧")
    print("=" * 60)
    for article in recommended:
        print()
        print(article.display())
    print()
    print("=" * 60)

    print("\n音声化する記事のIDを入力してください")
    print("例: 1,3,5  または  1-5  または  all（全おすすめ記事）")
    print("終了: q")

    while True:
        try:
            user_input = input("\n📎 記事ID> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します")
            break

        if user_input.lower() == "q":
            print("終了します")
            break

        if user_input.lower() == "all":
            selected_articles = recommended
        else:
            id_to_article = {a.id: a for a in articles}
            selected_ids = parse_selection(user_input, max(a.id for a in articles))
            selected_articles = [id_to_article[i] for i in selected_ids if i in id_to_article]

        if not selected_articles:
            print("⚠️  有効な記事が選択されていません。もう一度入力してください。")
            continue

        print(f"\n✅ {len(selected_articles)}件の記事を選択:")
        for a in selected_articles:
            print(f"  - [{a.id}] {a.title}")

        print("\n📝 ニュース原稿を生成中...")
        try:
            script = generate_news_script(selected_articles)
        except Exception as e:
            print(f"❌ 原稿生成エラー: {e}")
            continue

        print("\n--- 生成された原稿 ---")
        print(script)
        print("--- ここまで ---\n")

        if script_only:
            import os
            from datetime import datetime, timedelta, timezone
            from . import config
            jst = timezone(timedelta(hours=9))
            ts = datetime.now(jst).strftime("%Y%m%d_%H%M%S")
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            path = os.path.join(config.OUTPUT_DIR, f"news_digest_{ts}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(script)
            print(f"✅ 原稿を保存: {path}")
        else:
            print("🎵 音声ファイルを生成中...")
            try:
                audio_path = generate_audio(script)
                print(f"\n✅ 完了！出力: {audio_path}")
            except Exception as e:
                print(f"❌ 音声生成エラー: {e}")
                continue

        print("\n続けて別の記事を選択できます。終了するには q を入力してください。")


def auto_mode(top_n: int = 5, source: str = "rss", script_only: bool = False, from_file: str | None = None):
    print("=" * 60)
    print("📻 ニュースダイジェスト（自動モード）")
    print("=" * 60)
    print()

    articles = _fetch_articles(source, from_file)
    if not articles:
        print("❌ 記事が取得できませんでした")
        sys.exit(1)

    recommended = recommend_articles(articles, top_n=top_n)

    print(f"\n📋 上位{len(recommended)}件の記事で音声を生成します:")
    for a in recommended:
        print(f"  - [{a.id}] 【{a.source}】{a.title}")

    print("\n📝 ニュース原稿を生成中...")
    script = generate_news_script(recommended)

    print("\n--- 生成された原稿 ---")
    print(script)
    print("--- ここまで ---\n")

    if script_only:
        import os
        from datetime import datetime, timedelta, timezone
        from . import config
        jst = timezone(timedelta(hours=9))
        ts = datetime.now(jst).strftime("%Y%m%d_%H%M%S")
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        path = os.path.join(config.OUTPUT_DIR, f"news_digest_{ts}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"\n✅ 原稿を保存: {path}")
        return path
    else:
        print("🎵 音声ファイルを生成中...")
        audio_path = generate_audio(script)
        print(f"\n✅ 完了！出力: {audio_path}")
        return audio_path


def list_only(source: str = "rss", from_file: str | None = None):
    articles = _fetch_articles(source, from_file)
    if not articles:
        print("❌ 記事が取得できませんでした")
        sys.exit(1)

    print(f"\n📰 本日の記事一覧 ({len(articles)}件)")
    print("=" * 60)
    for article in articles:
        print()
        print(article.display())


def main():
    parser = argparse.ArgumentParser(description="ニュースダイジェスト音声生成ツール")
    parser.add_argument("--auto", action="store_true", help="自動モード（対話なし）")
    parser.add_argument("--top", type=int, default=5, help="自動モードで使う記事数 (default: 5)")
    parser.add_argument("--list-only", action="store_true", help="記事一覧を表示して終了")
    parser.add_argument("--source", choices=["rss", "newsapi"], default="rss",
                        help="ニュースソース (default: rss)")
    parser.add_argument("--script-only", action="store_true",
                        help="原稿のみ生成（音声生成をスキップ）")
    parser.add_argument("--from-file", type=str, default=None,
                        help="JSONファイルから記事を読み込み")
    args = parser.parse_args()

    if args.list_only:
        list_only(args.source, args.from_file)
    elif args.auto:
        auto_mode(args.top, args.source, args.script_only, args.from_file)
    else:
        interactive_mode(args.source, args.script_only, args.from_file)


if __name__ == "__main__":
    main()
