import json
import re
import sys
from pathlib import Path

ELA_FILE = Path("ELA.html")
CANDIDATE_FILE = Path("candidate-news.json")


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


def build_news_object(item):
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

    return f"""      {{
        title: {js_string(title)},
        description: {js_string(description)},
        link: {js_string(link)},
        date: {js_string(date)}
      }}"""


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

        selected_news.append(candidates[real_index])

    if not ELA_FILE.exists():
        raise FileNotFoundError("No se encontró ELA.html en la raíz del repositorio.")

    html = ELA_FILE.read_text(encoding="utf-8")

    if "const newsData = [" not in html:
        print("No se encontró 'const newsData = [' en ELA.html.")
        sys.exit(1)

    existing_links = set(
        normalize_url(match.group(1))
        for match in re.finditer(r"link:\s*[\"']([^\"']+)[\"']", html)
    )

    fresh_news = []

    for item in selected_news:
        link = normalize_url(item.get("link", ""))

        if not link:
            continue

        if link in existing_links:
            print(f"Duplicada, omitida: {item.get('title', '')}")
            continue

        fresh_news.append(item)

    if not fresh_news:
        print("No hay noticias nuevas que añadir.")
        return

    news_objects = ",\n".join(build_news_object(item) for item in fresh_news)

    updated_html = html.replace(
        "const newsData = [",
        f"const newsData = [\n{news_objects},",
        1
    )

    ELA_FILE.write_text(updated_html, encoding="utf-8")

    print(f"Añadidas {len(fresh_news)} noticias a ELA.html.")


if __name__ == "__main__":
    main()
