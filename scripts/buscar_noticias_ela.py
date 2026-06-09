import json
import re
import html
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

OUTPUT_FILE = Path("candidate-news.json")

QUERIES = [
    "ELA esclerosis lateral amiotrófica",
    "ley ELA prestación dependencia",
    "ELA pacientes cuidados copago",
    "ELA ensayo clínico fármaco",
    "esclerosis lateral amiotrófica España",
    "ELA investigación tratamiento",
]

MAX_ITEMS_PER_QUERY = 10
MAX_TOTAL_RESULTS = 30


def clean_text(value):
    if not value:
        return ""

    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_date(value):
    if not value:
        return ""

    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.date().isoformat()
    except Exception:
        return ""


def build_google_news_rss_url(query):
    encoded_query = urllib.parse.quote(query)
    return (
        "https://news.google.com/rss/search?"
        f"q={encoded_query}"
        "&hl=es"
        "&gl=ES"
        "&ceid=ES:es"
    )


def fetch_rss(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 ELA News Bot"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()

    return ET.fromstring(data)


def extract_items_from_feed(query, root):
    items = []

    for item in root.findall(".//item")[:MAX_ITEMS_PER_QUERY]:
        title = clean_text(item.findtext("title"))
        link = clean_text(item.findtext("link"))
        description = clean_text(item.findtext("description"))
        pub_date = parse_date(item.findtext("pubDate"))

        source_element = item.find("source")
        source = clean_text(source_element.text if source_element is not None else "Google News")

        if not title or not link:
            continue

        items.append({
            "title": title,
            "source": source,
            "date": pub_date,
            "link": link,
            "summary": description,
            "query": query,
            "relevance_reason": "Noticia encontrada en búsquedas relacionadas con ELA, cuidados, investigación, ley ELA o prestaciones."
        })

    return items


def main():
    all_items = []

    for query in QUERIES:
        url = build_google_news_rss_url(query)

        try:
            root = fetch_rss(url)
            items = extract_items_from_feed(query, root)
            all_items.extend(items)
        except Exception as error:
            print(f"Error buscando noticias para '{query}': {error}")

    seen = set()
    unique_items = []

    for item in all_items:
        key = item["link"]

        if key in seen:
            continue

        seen.add(key)
        unique_items.append(item)

    unique_items.sort(key=lambda item: item.get("date", ""), reverse=True)

    selected_items = unique_items[:MAX_TOTAL_RESULTS]

for index, item in enumerate(selected_items, start=1):
    item["id"] = index

output = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "total": len(selected_items),
    "news": selected_items
}

    OUTPUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Generado {OUTPUT_FILE} con {len(selected_items)} noticias candidatas.")


if __name__ == "__main__":
    main()
