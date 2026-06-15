import json
import re
import html
import difflib
import unicodedata
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


def normalize_for_match(value):
    value = clean_text(value).lower()
    value = unicodedata.normalize("NFD", value)
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def remove_source_suffix(value, source):
    value = clean_text(value)
    source = clean_text(source)

    if not value or not source:
        return value

    suffixes = [
        f" - {source}",
        f" – {source}",
        f" — {source}",
        f" | {source}",
        f" {source}",
    ]

    for suffix in suffixes:
        if value.lower().endswith(suffix.lower()):
            return value[:-len(suffix)].strip()

    return value


def is_repeated_summary(title, summary, source):
    summary_without_source = remove_source_suffix(summary, source)
    normalized_title = normalize_for_match(remove_source_suffix(title, source))
    normalized_summary = normalize_for_match(summary_without_source)

    if not normalized_title or not normalized_summary:
        return False

    if normalized_title == normalized_summary:
        return True

    similarity = difflib.SequenceMatcher(
        None,
        normalized_title,
        normalized_summary
    ).ratio()

    return similarity >= 0.92


def infer_topic(title, query):
    text = normalize_for_match(f"{title} {query}")

    if any(term in text for term in ["ley ela", "dependencia", "prestacion", "ayuda", "derecho"]):
        return "ley ELA, prestaciones, dependencia y derechos de las personas afectadas"

    if any(term in text for term in ["ensayo", "clinico", "farmaco", "tratamiento", "investigacion"]):
        return "investigación, ensayos clínicos y posibles tratamientos"

    if any(term in text for term in ["carrera", "solidari", "bicicleta", "reto", "visibilidad"]):
        return "iniciativas sociales, sensibilización y visibilidad pública de la ELA"

    if any(term in text for term in ["cuidados", "pacientes", "familia", "calidad de vida"]):
        return "cuidados, calidad de vida y acompañamiento a pacientes"

    return "actualidad relacionada con la ELA"


def build_context_summary(title, source, query, date):
    topic = infer_topic(title, query)
    source_text = f"Fuente: {source}." if source else "Fuente pendiente de confirmar."
    date_text = f" Publicada el {date}." if date else ""

    return (
        f"Aborda {topic}. {source_text}{date_text}"
    )


def prepare_summary(title, summary, source, query, date):
    summary = clean_text(summary)

    if summary and not is_repeated_summary(title, summary, source):
        return summary

    return build_context_summary(title, source, query, date)


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


def decode_html(data, response):
    charset = response.headers.get_content_charset() or "utf-8"

    try:
        return data.decode(charset, errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def extract_meta_description(page_html):
    meta_tags = re.findall(r"<meta\b[^>]*>", page_html, flags=re.IGNORECASE)
    wanted_names = ("description", "og:description", "twitter:description")

    for tag in meta_tags:
        normalized_tag = tag.lower()

        if not any(name in normalized_tag for name in wanted_names):
            continue

        content_match = re.search(
            r"\bcontent\s*=\s*(['\"])(.*?)\1",
            tag,
            flags=re.IGNORECASE | re.DOTALL
        )

        if content_match:
            return clean_text(content_match.group(2))

    return ""


def is_low_value_excerpt(excerpt, title, source):
    normalized_excerpt = normalize_for_match(excerpt)

    if len(normalized_excerpt) < 40:
        return True

    if is_repeated_summary(title, excerpt, source):
        return True

    low_value_patterns = [
        "google news",
        "news.google.com",
        "activa javascript",
        "enable javascript",
    ]

    return any(pattern in normalized_excerpt for pattern in low_value_patterns)


def fetch_article_excerpt(url, title, source):
    if not url:
        return ""

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 ELA News Bot"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            data = response.read(300000)
            page_html = decode_html(data, response)
    except Exception:
        return ""

    excerpt = extract_meta_description(page_html)

    if is_low_value_excerpt(excerpt, title, source):
        return ""

    return excerpt


def extract_items_from_feed(query, root):
    items = []

    for item in root.findall(".//item")[:MAX_ITEMS_PER_QUERY]:
        link = clean_text(item.findtext("link"))
        pub_date = parse_date(item.findtext("pubDate"))

        source_element = item.find("source")
        source = clean_text(
            source_element.text if source_element is not None else "Google News"
        )
        raw_title = clean_text(item.findtext("title"))
        title = remove_source_suffix(raw_title, source)
        rss_description = clean_text(item.findtext("description"))
        article_excerpt = fetch_article_excerpt(link, title, source)
        description = prepare_summary(
            title,
            article_excerpt or rss_description,
            source,
            query,
            pub_date
        )

        if not title or not link:
            continue

        items.append({
            "title": title,
            "source": source,
            "date": pub_date,
            "link": link,
            "summary": description,
            "query": query,
            "relevance_reason": (
                "Noticia encontrada en búsquedas relacionadas con ELA, "
                "cuidados, investigación, ley ELA o prestaciones."
            )
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
