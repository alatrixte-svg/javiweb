import json
import os
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
from zoneinfo import ZoneInfo

OUTPUT_FILE = Path(os.environ.get("ELA_NEWS_OUTPUT", "candidate-news.json"))
LOCAL_TIMEZONE = ZoneInfo("Europe/Madrid")
WEEKLY_SOURCES_ENV = "ELA_NEWS_FORCE_WEEKLY_SOURCES"

QUERIES = [
    "ELA esclerosis lateral amiotrófica",
    "ley ELA prestación dependencia",
    "ELA pacientes cuidados copago",
    "ELA ensayo clínico fármaco",
    "esclerosis lateral amiotrófica España",
    "ELA investigación tratamiento",
]

MAX_ITEMS_PER_QUERY = 10
MAX_TOTAL_RESULTS = 60

INTERNATIONAL_QUERIES = [
    "ALS amyotrophic lateral sclerosis treatment research",
    "ALS clinical trial therapy diagnosis",
    "motor neuron disease ALS patients care",
]

GDELT_QUERIES = [
    '("ELA" OR "esclerosis lateral amiotrofica" OR "esclerosis lateral amiotrófica") '
    '(España OR español OR pacientes OR investigación OR tratamiento)',
    '("ley ELA" OR "ayudas ELA" OR "copago ELA" OR "dependencia ELA")',
]

CURATED_RSS_FEEDS = [
    {
        "name": "ALS News Today",
        "url": "https://alsnewstoday.com/feed/",
        "query": "RSS curado ALS investigación tratamiento",
    },
]

CURATED_RSS_KEYWORDS = [
    "ela",
    "als",
    "amyotrophic lateral sclerosis",
    "esclerosis lateral amiotrofica",
    "esclerosis lateral amiotrófica",
    "motor neurone disease",
    "motor neuron disease",
]

WEDNESDAY_HTML_SOURCES = [
    {
        "name": "ELA Andalucia",
        "url": "https://www.elaandalucia.es/noticias/",
        "query": "ELA Andalucia noticias",
        "provider": "ela_andalucia",
    },
]

SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


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


def parse_page_date(value):
    text = normalize_for_match(value)

    match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
    if match:
        return match.group(0)

    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", text)
    if match:
        day, month, year = (int(part) for part in match.groups())

        try:
            return datetime(year, month, day).date().isoformat()
        except ValueError:
            return ""

    match = re.search(
        r"\b(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})\b",
        text
    )
    if match:
        day = int(match.group(1))
        month = SPANISH_MONTHS.get(match.group(2))
        year = int(match.group(3))

        if month:
            try:
                return datetime(year, month, day).date().isoformat()
            except ValueError:
                return ""

    return ""


def should_include_wednesday_sources():
    forced_value = os.environ.get(WEEKLY_SOURCES_ENV)

    if forced_value is not None:
        return normalize_for_match(forced_value) in {"1", "true", "yes", "si"}

    return datetime.now(LOCAL_TIMEZONE).weekday() == 2


def fetch_page_html(url, timeout=20, read_limit=500000):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 ELA News Bot"
        }
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read(read_limit)
        return decode_html(data, response)


def build_google_news_rss_url(query, international=False):
    encoded_query = urllib.parse.quote(query)
    language, country, edition = ("en", "US", "US:en") if international else ("es", "ES", "ES:es")
    return (
        "https://news.google.com/rss/search?"
        f"q={encoded_query}"
        f"&hl={language}"
        f"&gl={country}"
        f"&ceid={edition}"
    )


def build_gdelt_doc_url(query):
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(MAX_ITEMS_PER_QUERY),
        "sort": "HybridRel",
        "timespan": "7d",
    }

    return "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(params)


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


def fetch_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 ELA News Bot"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read()
        page_text = decode_html(data, response)

    return json.loads(page_text)


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


def is_probable_news_anchor(base_url, link, title):
    normalized_title = normalize_for_match(title)

    if len(normalized_title) < 18:
        return False

    ignored_titles = [
        "leer mas",
        "ver mas",
        "inicio",
        "contacto",
        "politica de privacidad",
        "politica de cookies",
        "politica de calidad",
        "aviso legal",
        "canal de denuncias",
        "cookies",
        "buscar",
        "donar",
        "hazte socio",
        "facebook",
        "twitter",
        "instagram",
        "youtube",
    ]

    if normalized_title in ignored_titles:
        return False

    parsed_base = urllib.parse.urlparse(base_url)
    parsed_link = urllib.parse.urlparse(link)

    if parsed_link.scheme and parsed_link.scheme not in {"http", "https"}:
        return False

    if parsed_link.netloc and parsed_link.netloc != parsed_base.netloc:
        return False

    normalized_base_path = parsed_base.path.rstrip("/")
    normalized_link_path = parsed_link.path.rstrip("/")

    if not normalized_link_path or normalized_link_path == normalized_base_path:
        return False

    if "noticia" in normalize_for_match(normalized_link_path):
        return True

    return True


def extract_items_from_html_news_source(source_config):
    source_name = source_config["name"]
    source_url = source_config["url"]
    source_query = source_config["query"]
    source_provider = source_config["provider"]
    page_html = fetch_page_html(source_url)
    items = []
    seen_links = set()
    anchor_pattern = re.compile(
        r"<a\b[^>]*href\s*=\s*(['\"])(.*?)\1[^>]*>(.*?)</a>",
        flags=re.IGNORECASE | re.DOTALL
    )
    anchors = list(anchor_pattern.finditer(page_html))
    link_counts = {}

    for match in anchors:
        link = urllib.parse.urljoin(source_url, clean_text(match.group(2)))
        title = clean_text(match.group(3))

        if len(normalize_for_match(title)) >= 18:
            link_counts[link] = link_counts.get(link, 0) + 1

    for match in anchors:
        raw_link = clean_text(match.group(2))
        title = clean_text(match.group(3))
        link = urllib.parse.urljoin(source_url, raw_link)

        if (
            link in seen_links
            or link_counts.get(link, 0) > 1
            or not is_probable_news_anchor(source_url, link, title)
        ):
            continue

        seen_links.add(link)
        context_start = max(0, match.start() - 600)
        context_end = min(len(page_html), match.end() + 600)
        context = page_html[context_start:context_end]
        date = parse_page_date(context)
        article_excerpt = fetch_article_excerpt(link, title, source_name)

        built_item = build_news_item(
            title,
            source_name,
            date or datetime.now(LOCAL_TIMEZONE).date().isoformat(),
            link,
            article_excerpt,
            source_query,
            source_provider
        )

        if built_item:
            items.append(built_item)

        if len(items) >= MAX_ITEMS_PER_QUERY:
            break

    return items


def item_matches_curated_keywords(title, summary=""):
    text = normalize_for_match(f"{title} {summary}")

    return any(
        normalize_for_match(keyword) in text
        for keyword in CURATED_RSS_KEYWORDS
    )


def build_news_item(title, source, date, link, summary, query, provider):
    title = remove_source_suffix(title, source)
    description = prepare_summary(title, summary, source, query, date)

    if not title or not link:
        return None

    return {
        "title": title,
        "source": source,
        "date": date,
        "link": link,
        "summary": description,
        "query": query,
        "provider": provider,
        "relevance_reason": (
            "Noticia encontrada en búsquedas relacionadas con ELA, "
            "cuidados, investigación, ley ELA, prestaciones o ALS."
        )
    }


def extract_items_from_feed(query, root, section="spain"):
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

        item_section = section
        if normalize_for_match(source) == "als news today":
            item_section = "international"

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
            ),
            "section": item_section
        })

    return items


def parse_gdelt_date(value):
    if not value:
        return ""

    value = str(value)

    if len(value) >= 8:
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"

    return ""


def extract_items_from_gdelt(query, data):
    items = []

    for article in data.get("articles", [])[:MAX_ITEMS_PER_QUERY]:
        title = clean_text(article.get("title", ""))
        link = clean_text(article.get("url", ""))
        source = clean_text(
            article.get("sourceCommonName", "")
            or article.get("domain", "")
            or "GDELT"
        )
        date = parse_gdelt_date(article.get("seendate", ""))
        article_excerpt = fetch_article_excerpt(link, title, source)
        built_item = build_news_item(
            title,
            source,
            date,
            link,
            article_excerpt,
            query,
            "gdelt"
        )

        if built_item:
            items.append(built_item)

    return items


def extract_items_from_curated_feed(feed):
    items = []
    root = fetch_rss(feed["url"])
    channel_title = clean_text(root.findtext(".//channel/title"))

    for item in root.findall(".//item")[:MAX_ITEMS_PER_QUERY]:
        link = clean_text(item.findtext("link"))
        title = clean_text(item.findtext("title"))
        rss_description = clean_text(item.findtext("description"))

        if not item_matches_curated_keywords(title, rss_description):
            continue

        source = feed.get("name") or channel_title or "RSS curado"
        date = parse_date(item.findtext("pubDate"))
        article_excerpt = fetch_article_excerpt(link, title, source)
        built_item = build_news_item(
            title,
            source,
            date,
            link,
            article_excerpt or rss_description,
            feed.get("query", source),
            "curated_rss"
        )

        if built_item:
            items.append(built_item)

    return items


def main():
    all_items = []
    provider_counts = {}

    def add_items(provider, items):
        for item in items:
            item.setdefault("provider", provider)

        provider_counts[provider] = provider_counts.get(provider, 0) + len(items)
        all_items.extend(items)

    if should_include_wednesday_sources():
        for source_config in WEDNESDAY_HTML_SOURCES:
            try:
                items = extract_items_from_html_news_source(source_config)
                add_items(source_config["provider"], items)
            except Exception as error:
                print(f"Error leyendo fuente semanal '{source_config['name']}': {error}")

    for query in QUERIES:
        url = build_google_news_rss_url(query)

        try:
            root = fetch_rss(url)
            items = extract_items_from_feed(query, root, "spain")
            add_items("google_news", items)
        except Exception as error:
            print(f"Error buscando noticias para '{query}': {error}")

    for query in INTERNATIONAL_QUERIES:
        url = build_google_news_rss_url(query, international=True)

        try:
            root = fetch_rss(url)
            items = extract_items_from_feed(query, root, "international")
            add_items("google_news_international", items)
        except Exception as error:
            print(f"Error buscando noticias internacionales para '{query}': {error}")

    for query in GDELT_QUERIES:
        url = build_gdelt_doc_url(query)

        try:
            data = fetch_json(url)
            items = extract_items_from_gdelt(query, data)
            add_items("gdelt", items)
        except Exception as error:
            print(f"Error buscando noticias en GDELT para '{query}': {error}")

    for feed in CURATED_RSS_FEEDS:
        try:
            items = extract_items_from_curated_feed(feed)
            add_items("curated_rss", items)
        except Exception as error:
            print(f"Error leyendo RSS curado '{feed['name']}': {error}")

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
        "providers": provider_counts,
        "total": len(selected_items),
        "news": selected_items
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Generado {OUTPUT_FILE} con {len(selected_items)} noticias candidatas.")
    print("Fuentes consultadas:", json.dumps(provider_counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
