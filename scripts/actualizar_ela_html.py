import json
import re
import sys
import difflib
import unicodedata
from pathlib import Path

ELA_FILE = Path("ELA.html")
CANDIDATE_FILE = Path("candidate-news.json")
BACKUP_CANDIDATE_FILE = Path("candidate-news.backup.json")
MAX_NEWS_IN_ELA = 30


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
        f" {source}",
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


def sort_key(item):
    return item.get("date", "") or ""


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

    ELA_FILE.write_text(updated_html, encoding="utf-8")

    removed_count = max(0, len(unique_news) - len(limited_news))

    print(f"Noticias actuales antes de actualizar: {len(current_news)}")
    print(f"Noticias descartadas retiradas de ELA.html: {len(current_news) - len(current_news_after_discards)}")
    print(f"Noticias seleccionadas: {len(selected_news)}")
    print(f"Noticias guardadas finalmente en ELA.html: {len(limited_news)}")
    print(f"Noticias eliminadas por superar el límite de {MAX_NEWS_IN_ELA}: {removed_count}")
    print(f"Límite máximo configurado: {MAX_NEWS_IN_ELA}")


if __name__ == "__main__":
    main()
