import json
import re
import sys
from pathlib import Path

ELA_FILE = Path("ELA.html")
CANDIDATE_FILE = Path("candidate-news.json")
MAX_NEWS_IN_ELA = 30


def js_string(value):
    return json.dumps(value or "", ensure_ascii=False)


def normalize_url(url):
    return (url or "").strip()


def load_candidates():
    if not CANDIDATE_FILE.exists():
        raise FileNotFoundError(
            "No existe candidate-news.json. Ejecuta primero la búsqueda de noticias."
        )

    data = json.loads(CANDIDATE_FILE.read_text(encoding="utf-8"))
    return data.get("news", [])


def clean_candidate_item(item):
    title = item.get("title", "").strip()
    source = item.get("source", "").strip()
    summary = item.get("summary", "").strip()
    link = item.get("link", "").strip()
    date = item.get("date", "").strip()

    if source and source not in title:
        description = f"Noticia de {source}. {summary}"
    else:
        description = summary

    if not description:
        description = (
            "Noticia relacionada con la ELA, sus pacientes, investigación, "
            "cuidados, prestaciones o derechos."
        )

    return {
        "title": title,
        "description": description,
        "link": link,
        "date": date
    }


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

    current_news = extract_current_news(html)

    combined_news = selected_news + current_news

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
    print(f"Noticias seleccionadas: {len(selected_news)}")
    print(f"Noticias guardadas finalmente en ELA.html: {len(limited_news)}")
    print(f"Noticias eliminadas por superar el límite de {MAX_NEWS_IN_ELA}: {removed_count}")
    print(f"Límite máximo configurado: {MAX_NEWS_IN_ELA}")


if __name__ == "__main__":
    main()
