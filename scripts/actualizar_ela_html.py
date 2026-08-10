import json
import re
import sys
import difflib
import unicodedata
from pathlib import Path

ELA_FILE = Path("ELA.html")
CANDIDATE_FILE = Path("candidate-news.json")
BACKUP_CANDIDATE_FILE = Path("candidate-news.backup.json")
MAX_NEWS_IN_ELA = 15
MAX_INTERNATIONAL_NEWS_IN_ELA = 6
SOCIAL_MESSAGE_URL = "https://javiergamezmartin.com/ELA.html"
SOCIAL_MESSAGE_TITLE_COUNT = 4
EXCLUDED_NEWS_TITLE_FRAGMENTS = (
    "juanjo miranda",
    "cazadores de almeria",
    "ataxia de friedreich",
)
TITLE_STOPWORDS = {
    "a", "al", "ante", "bajo", "con", "contra", "de", "del", "desde",
    "durante", "e", "el", "en", "entre", "es", "esa", "ese", "esta",
    "este", "la", "las", "lo", "los", "mas", "para", "por", "que",
    "se", "sin", "sobre", "su", "sus", "un", "una", "unas", "unos", "y"
}

def js_string(value):
    return json.dumps(value or "", ensure_ascii=False)


def normalize_url(url):
    return (url or "").strip()


def clean_text(value):
    value = value or ""
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
    ]

    for suffix in suffixes:
        if value.lower().endswith(suffix.lower()):
            return value[:-len(suffix)].strip()

    return value


def infer_source_from_title(title):
    parts = re.split(r"\s[-–—|]\s", clean_text(title))

    if len(parts) < 2:
        return ""

    source = parts[-1].strip()

    if 2 <= len(source) <= 60:
        return source

    return ""


def infer_source_from_description(description):
    match = re.search(
        r"Fuente:\s*(.*?)(?:\.\s*Publicada|\.$)",
        clean_text(description)
    )

    if match:
        return match.group(1).strip()

    return ""


def is_repeated_description(title, description, source):
    normalized_title = normalize_for_match(remove_source_suffix(title, source))
    normalized_description = normalize_for_match(
        remove_source_suffix(description, source)
    )

    if not normalized_title or not normalized_description:
        return False

    if normalized_title == normalized_description:
        return True

    similarity = difflib.SequenceMatcher(
        None,
        normalized_title,
        normalized_description
    ).ratio()

    return similarity >= 0.92


def infer_topic(title, query=""):
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


def build_context_description(title, source, query, date):
    topic = infer_topic(title, query)
    source_text = f"Fuente: {source}." if source else "Fuente pendiente de confirmar."
    date_text = f" Publicada el {date}." if date else ""

    return f"Aborda {topic}. {source_text}{date_text}"


def sanitize_news_item(item):
    raw_title = clean_text(item.get("title", ""))
    raw_description = clean_text(item.get("description", "") or item.get("summary", ""))
    source = (
        clean_text(item.get("source", ""))
        or infer_source_from_title(raw_title)
        or infer_source_from_description(raw_description)
    )
    query = clean_text(item.get("query", ""))
    date = clean_text(item.get("date", ""))
    title = remove_source_suffix(raw_title, source)
    description = raw_description

    if (
        not description
        or description.startswith("Aborda ")
        or is_repeated_description(title, description, source)
    ):
        description = build_context_description(title, source, query, date)

    return {
        "title": title,
        "source": source,
        "description": description,
        "link": clean_text(item.get("link", "")),
        "date": date
    }


def load_candidates():
    if not CANDIDATE_FILE.exists():
        raise FileNotFoundError(
            "No existe candidate-news.json. Ejecuta primero la búsqueda de noticias."
        )

    data = json.loads(CANDIDATE_FILE.read_text(encoding="utf-8"))
    return data.get("news", [])


def load_backup_candidates():
    if not BACKUP_CANDIDATE_FILE.exists():
        return []

    data = json.loads(BACKUP_CANDIDATE_FILE.read_text(encoding="utf-8"))
    return data.get("news", [])


def get_discarded_candidate_links(candidates):
    reviewed_links = {
        normalize_url(item.get("link", ""))
        for item in candidates
        if normalize_url(item.get("link", ""))
    }

    discarded_links = set()

    for item in load_backup_candidates():
        link = normalize_url(item.get("link", ""))

        if link and link not in reviewed_links:
            discarded_links.add(link)

    return discarded_links


def clean_candidate_item(item):
    return sanitize_news_item(item)


def is_excluded_news(item):
    title = normalize_for_match(item.get("title", ""))
    return any(fragment in title for fragment in EXCLUDED_NEWS_TITLE_FRAGMENTS)

def extract_current_news(html):
    match = re.search(
        r"const\s+newsData\s*=\s*\[(.*?)\];",
        html,
        flags=re.DOTALL
    )

    if not match:
        print("No se encontró el array newsData en ELA.html.")
        sys.exit(1)

    array_content = match.group(1)

    object_pattern = re.compile(
        r"\{\s*"
        r"title:\s*(?P<title>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')\s*,\s*"
        r"(?:source:\s*(?P<source>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')\s*,\s*)?"
        r"description:\s*(?P<description>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')\s*,\s*"
        r"link:\s*(?P<link>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')\s*,\s*"
        r"date:\s*(?P<date>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')\s*"
        r"\}",
        flags=re.DOTALL
    )

    current_news = []

    for object_match in object_pattern.finditer(array_content):
        try:
            current_news.append({
                "title": json.loads(object_match.group("title")),
                "source": (
                    json.loads(object_match.group("source"))
                    if object_match.group("source")
                    else ""
                ),
                "description": json.loads(object_match.group("description")),
                "link": json.loads(object_match.group("link")),
                "date": json.loads(object_match.group("date"))
            })
        except json.JSONDecodeError:
            continue

    return current_news


def build_news_object(item):
    return f"""      {{
        title: {js_string(item.get("title", ""))},
        source: {js_string(item.get("source", ""))},
        description: {js_string(item.get("description", ""))},
        link: {js_string(item.get("link", ""))},
        date: {js_string(item.get("date", ""))}
      }}"""


def replace_news_array(html, news):
    news_objects = ",\n".join(build_news_object(item) for item in news)

    new_array = f"const newsData = [\n{news_objects}\n    ];"

    updated_html = re.sub(
        r"const\s+newsData\s*=\s*\[.*?\];",
        new_array,
        html,
        count=1,
        flags=re.DOTALL
    )

    return updated_html


def extract_current_international_news(html):
    match = re.search(r"const\s+internationalNewsData\s*=\s*\[(.*?)\];", html, flags=re.DOTALL)
    if not match:
        return []

    object_pattern = re.compile(
        r"\{\s*title:\s*(?P<title>\"(?:\\.|[^\"\\])*\")\s*,\s*"
        r"source:\s*(?P<source>\"(?:\\.|[^\"\\])*\")\s*,\s*"
        r"description:\s*(?P<description>\"(?:\\.|[^\"\\])*\")\s*,\s*"
        r"link:\s*(?P<link>\"(?:\\.|[^\"\\])*\")\s*,\s*"
        r"date:\s*(?P<date>\"(?:\\.|[^\"\\])*\")\s*\}",
        flags=re.DOTALL
    )
    current_news = []
    for object_match in object_pattern.finditer(match.group(1)):
        try:
            current_news.append({
                key: json.loads(object_match.group(key))
                for key in ("title", "source", "description", "link", "date")
            })
        except json.JSONDecodeError:
            continue
    return current_news


def replace_international_news_array(html, news):
    news_objects = ",\n".join(build_news_object(item) for item in news)
    new_array = f"const internationalNewsData = [\n{news_objects}\n    ];"
    return re.sub(
        r"const\s+internationalNewsData\s*=\s*\[.*?\];",
        new_array,
        html,
        count=1,
        flags=re.DOTALL
    )


def sort_key(item):
    return item.get("date", "") or ""


def title_tokens(title):
    normalized = normalize_for_match(title)
    return {
        token
        for token in normalized.split()
        if len(token) > 2 and token not in TITLE_STOPWORDS
    }


def titles_are_related(left, right):
    left_normalized = normalize_for_match(left)
    right_normalized = normalize_for_match(right)

    if not left_normalized or not right_normalized:
        return False

    if left_normalized == right_normalized:
        return True

    similarity = difflib.SequenceMatcher(
        None,
        left_normalized,
        right_normalized
    ).ratio()

    if similarity >= 0.68:
        return True

    left_tokens = title_tokens(left)
    right_tokens = title_tokens(right)

    if not left_tokens or not right_tokens:
        return False

    common_tokens = left_tokens & right_tokens
    token_ratio = len(common_tokens) / len(left_tokens | right_tokens)

    if len(common_tokens) >= 4:
        return True

    return len(common_tokens) >= 3 and token_ratio >= 0.34


def pick_social_message_titles(news):
    groups = []

    for position, item in enumerate(news):
        title = clean_text(item.get("title", ""))

        if not title:
            continue

        matched_group = None

        for group in groups:
            if any(titles_are_related(title, member["title"]) for member in group["items"]):
                matched_group = group
                break

        if matched_group:
            matched_group["items"].append({"title": title, "position": position})
        else:
            groups.append({
                "items": [{"title": title, "position": position}],
                "first_position": position
            })

    repeated_groups = [
        group for group in groups if len(group["items"]) > 1
    ]

    if repeated_groups:
        repeated_groups.sort(
            key=lambda group: (-len(group["items"]), group["first_position"])
        )
        chosen = [
            group["items"][0]["title"]
            for group in repeated_groups[:SOCIAL_MESSAGE_TITLE_COUNT]
        ]

        if len(chosen) < SOCIAL_MESSAGE_TITLE_COUNT:
            used_titles = set(chosen)
            remaining_items = []

            for position, item in enumerate(news):
                title = clean_text(item.get("title", ""))

                if not title or title in used_titles:
                    continue

                if any(titles_are_related(title, used_title) for used_title in used_titles):
                    continue

                remaining_items.append({
                    "title": title,
                    "position": position
                })

            remaining_items.sort(
                key=lambda item: item["position"]
            )

            for item in remaining_items:
                chosen.append(item["title"])
                used_titles.add(item["title"])

                if len(chosen) == SOCIAL_MESSAGE_TITLE_COUNT:
                    break

            if len(chosen) < SOCIAL_MESSAGE_TITLE_COUNT:
                for item in news:
                    title = clean_text(item.get("title", ""))
                    if title and title not in used_titles:
                        chosen.append(title)
                        used_titles.add(title)
                    if len(chosen) == SOCIAL_MESSAGE_TITLE_COUNT:
                        break

        return chosen[:SOCIAL_MESSAGE_TITLE_COUNT]

    return [
        clean_text(item.get("title", ""))
        for item in news
        if clean_text(item.get("title", ""))
    ][:SOCIAL_MESSAGE_TITLE_COUNT]


def prioritize_recent_news(news, minimum_items=SOCIAL_MESSAGE_TITLE_COUNT):
    dated_news = [
        item for item in news
        if clean_text(item.get("date", ""))
    ]

    if not dated_news:
        return news

    dates = sorted(
        {clean_text(item.get("date", "")) for item in dated_news},
        reverse=True
    )
    recent_news = []

    for date in dates:
        recent_news.extend(
            item for item in news
            if clean_text(item.get("date", "")) == date
        )

        if len(recent_news) >= minimum_items:
            return recent_news

    return recent_news


def build_social_message(news):
    recent_news = prioritize_recent_news(news)
    titles = pick_social_message_titles(recent_news)
    topic_text = " y ".join(f"<{title}>" for title in titles)

    if not topic_text:
        topic_text = "la actualidad relacionada con la ELA"

    return (
        "Buenos días,\n"
        "\n"
        "Actualización diaria de las noticias sobre #ELA.\n"
        f"Lo más novedoso se centra en {topic_text}.\n"
        "\n"
        f"{SOCIAL_MESSAGE_URL}"
    )


def print_social_message_box(message):
    print("")
    print("+" + "=" * 70 + "+")
    print("| CAJETÍN DE TEXTO PARA COMPARTIR" + " " * 38 + "|")
    print("+" + "=" * 70 + "+")
    print(message)
    print("+" + "=" * 70 + "+")


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/actualizar_ela_html.py 1,3,5")
        sys.exit(1)

    selected_arg = sys.argv[1].strip()

    if not selected_arg:
        print("No se indicaron noticias seleccionadas.")
        sys.exit(1)

    selected_indexes = []

    for part in selected_arg.split(","):
        part = part.strip()

        if not part:
            continue

        try:
            selected_indexes.append(int(part))
        except ValueError:
            print(f"Índice inválido: {part}")
            sys.exit(1)

    candidates = load_candidates()
    discarded_candidate_links = get_discarded_candidate_links(candidates)

    if not candidates:
        print("candidate-news.json no contiene noticias.")
        sys.exit(1)

    selected_news = []

    for index in selected_indexes:
        real_index = index - 1

        if real_index < 0 or real_index >= len(candidates):
            print(f"El índice {index} no existe en candidate-news.json.")
            sys.exit(1)

        selected_news.append(clean_candidate_item(candidates[real_index]))

    if not ELA_FILE.exists():
        raise FileNotFoundError("No se encontró ELA.html en la raíz del repositorio.")

    html = ELA_FILE.read_text(encoding="utf-8")

    current_news = [
        sanitize_news_item(item)
        for item in extract_current_news(html)
    ]
    current_news_after_discards = [
        item
        for item in current_news
        if normalize_url(item.get("link", "")) not in discarded_candidate_links
        and not is_excluded_news(item)
    ]

    combined_news = selected_news + current_news_after_discards

    unique_news = []
    seen_links = set()

    for item in combined_news:
        link = normalize_url(item.get("link", ""))

        if not link:
            continue

        if link in seen_links:
            continue

        seen_links.add(link)
        unique_news.append(item)

    unique_news.sort(key=sort_key, reverse=True)

    limited_news = unique_news[:MAX_NEWS_IN_ELA]

    updated_html = replace_news_array(html, limited_news)

    current_international_news = extract_current_international_news(html)
    international_candidates = [
        clean_candidate_item(item)
        for item in candidates
        if item.get("section") == "international"
    ]
    international_candidates.sort(key=sort_key, reverse=True)

    international_news = []
    seen_international_links = set()
    seen_international_titles = []
    for item in international_candidates + current_international_news:
        link = normalize_url(item.get("link", ""))
        title = clean_text(item.get("title", ""))
        if (
            not link
            or link in seen_international_links
            or any(titles_are_related(title, previous) for previous in seen_international_titles)
        ):
            continue
        seen_international_links.add(link)
        seen_international_titles.append(title)
        international_news.append(item)
        if len(international_news) == MAX_INTERNATIONAL_NEWS_IN_ELA:
            break

    updated_html = replace_international_news_array(updated_html, international_news)

    ELA_FILE.write_text(updated_html, encoding="utf-8")

    removed_count = max(0, len(unique_news) - len(limited_news))

    print(f"Noticias actuales antes de actualizar: {len(current_news)}")
    print(f"Noticias descartadas retiradas de ELA.html: {len(current_news) - len(current_news_after_discards)}")
    print(f"Noticias seleccionadas: {len(selected_news)}")
    print(f"Noticias guardadas finalmente en ELA.html: {len(limited_news)}")
    print(f"Noticias internacionales guardadas finalmente en ELA.html: {len(international_news)}")
    print(f"Noticias eliminadas por superar el límite de {MAX_NEWS_IN_ELA}: {removed_count}")
    print(f"Límite máximo configurado: {MAX_NEWS_IN_ELA}")
    print_social_message_box(build_social_message(limited_news))


if __name__ == "__main__":
    main()
