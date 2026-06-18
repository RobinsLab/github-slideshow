import xml.etree.ElementTree as ET
import urllib.request
import re
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from email.utils import parsedate_to_datetime


@dataclass
class Article:
    title: str
    summary: str
    link: str
    source: str
    category: str
    published: str
    id: int = 0

    def display(self) -> str:
        summary_preview = self.summary[:120] + "..." if len(self.summary) > 120 else self.summary
        return (
            f"[{self.id}] 【{self.source} - {self.category}】\n"
            f"    {self.title}\n"
            f"    {summary_preview}\n"
            f"    {self.link}\n"
            f"    {self.published}"
        )


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _parse_rss(xml_text: str) -> list[dict]:
    entries = []
    root = ET.fromstring(xml_text)

    ns = {}
    for prefix in ["dc", "content", "rdf"]:
        for elem in root.iter():
            for key, val in elem.attrib.items():
                if key.startswith("{"):
                    pass
            break

    rdf_ns = {"rdf": "http://purl.org/rss/1.0/", "dc": "http://purl.org/dc/elements/1.1/"}

    # RSS 2.0
    for item in root.iter("item"):
        entry = {}
        title_el = item.find("title")
        if title_el is None:
            title_el = item.find("rdf:title", rdf_ns)
        entry["title"] = title_el.text if title_el is not None and title_el.text else ""

        link_el = item.find("link")
        if link_el is None:
            link_el = item.find("rdf:link", rdf_ns)
        entry["link"] = link_el.text if link_el is not None and link_el.text else ""

        desc_el = item.find("description")
        if desc_el is None:
            desc_el = item.find("rdf:description", rdf_ns)
        entry["description"] = _strip_html(desc_el.text) if desc_el is not None and desc_el.text else ""

        pub_el = item.find("pubDate")
        if pub_el is None:
            pub_el = item.find("dc:date", rdf_ns)
        entry["pubDate"] = pub_el.text if pub_el is not None and pub_el.text else ""

        entries.append(entry)

    # RDF/RSS 1.0
    if not entries:
        for item in root.findall("{http://purl.org/rss/1.0/}item"):
            entry = {}
            t = item.find("{http://purl.org/rss/1.0/}title")
            entry["title"] = t.text if t is not None and t.text else ""
            l = item.find("{http://purl.org/rss/1.0/}link")
            entry["link"] = l.text if l is not None and l.text else ""
            d = item.find("{http://purl.org/rss/1.0/}description")
            entry["description"] = _strip_html(d.text) if d is not None and d.text else ""
            p = item.find("{http://purl.org/dc/elements/1.1/}date")
            entry["pubDate"] = p.text if p is not None and p.text else ""
            entries.append(entry)

    return entries


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        pass
    for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    try:
        clean = re.sub(r"\+(\d{2}):(\d{2})$", r"+\1\2", date_str)
        return datetime.fromisoformat(clean)
    except Exception:
        return None


def fetch_rss(feeds: dict[str, str], source_name: str) -> list[Article]:
    articles = []
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst).date()

    for category, url in feeds.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "NewsDigestBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_text = resp.read().decode("utf-8", errors="replace")

            entries = _parse_rss(xml_text)

            for entry in entries:
                pub_date_str = ""
                dt = _parse_date(entry.get("pubDate", ""))
                if dt:
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    entry_date = dt.astimezone(jst).date()
                    if entry_date < today - timedelta(days=1):
                        continue
                    pub_date_str = dt.astimezone(jst).strftime("%Y-%m-%d %H:%M")

                articles.append(Article(
                    title=entry.get("title", "No title"),
                    summary=entry.get("description", ""),
                    link=entry.get("link", ""),
                    source=source_name,
                    category=category,
                    published=pub_date_str,
                ))
        except Exception as e:
            print(f"  [WARN] {source_name}/{category} の取得に失敗: {e}")

    return articles


def fetch_all_articles() -> list[Article]:
    from . import config

    print("📰 日経新聞のRSSを取得中...")
    nikkei = fetch_rss(config.NIKKEI_RSS_FEEDS, "日経新聞")
    print(f"  → {len(nikkei)}件取得")

    print("📰 WSJのRSSを取得中...")
    wsj = fetch_rss(config.WSJ_RSS_FEEDS, "WSJ")
    print(f"  → {len(wsj)}件取得")

    all_articles = nikkei + wsj
    for i, article in enumerate(all_articles, 1):
        article.id = i

    return all_articles
