import json
import re
import sys
import unicodedata
from pathlib import Path

BLOG_POSTS_FILE = Path("blog-posts.json")
POSTS_DIR = Path("posts")


def slugify(text):
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


def load_article(path):
    if not Path(path).exists():
        print(f"No existe el archivo de entrada: {path}")
        sys.exit(1)

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        print("El JSON del artículo no es válido.")
        print(error)
        sys.exit(1)


def get_value(article, *keys, default=""):
    for key in keys:
        if key in article and article[key] not in [None, ""]:
            return article[key]
    return default


def escape_frontmatter(value):
    value = str(value or "")
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    return value


def build_markdown(article, article_id, title, date_iso, fecha, tag, excerpt, body):
    frontmatter = f"""---
id: "{escape_frontmatter(article_id)}"
title: "{escape_frontmatter(title)}"
date: "{escape_frontmatter(date_iso)}"
fecha: "{escape_frontmatter(fecha)}"
tag: "{escape_frontmatter(tag)}"
excerpt: "{escape_frontmatter(excerpt)}"
---

"""

    if isinstance(body, list):
        markdown_body = "\n\n".join(str(paragraph).strip() for paragraph in body if str(paragraph).strip())
    else:
        markdown_body = str(body or "").strip()

    return frontmatter + markdown_body + "\n"


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/publicar_blog_post.py draft-blog-post.json")
        sys.exit(1)

    input_file = sys.argv[1]
    article = load_article(input_file)

    title = get_value(article, "titulo", "title")
    fecha = get_value(article, "fecha")
    date_iso = get_value(article, "date", "fecha_iso")
    excerpt = get_value(article, "extracto", "excerpt")
    tag = get_value(article, "etiqueta", "tag", default="Blog")
    body = get_value(article, "cuerpo", "body", "markdown", default=[])

    if not title:
        print("Falta el título del artículo.")
        sys.exit(1)

    if not fecha:
        print("Falta la fecha visible del artículo. Ejemplo: 7 de junio de 2026")
        sys.exit(1)

    if not date_iso:
        print("Falta la fecha ISO del artículo. Ejemplo: 2026-06-07")
        sys.exit(1)

    if not body:
        print("Falta el cuerpo del artículo.")
        sys.exit(1)

    slug = slugify(title)
    article_id = get_value(article, "id", default=f"post-{slug}")
    markdown_filename = f"{date_iso}-{slug}.md"
    markdown_path = POSTS_DIR / markdown_filename

    if not BLOG_POSTS_FILE.exists():
        print("No se encontró blog-posts.json en la raíz del repositorio.")
        sys.exit(1)

    POSTS_DIR.mkdir(exist_ok=True)

    blog_posts = json.loads(BLOG_POSTS_FILE.read_text(encoding="utf-8"))

    if not isinstance(blog_posts, list):
        print("blog-posts.json debe contener un array de artículos.")
        sys.exit(1)

    existing_ids = {post.get("id") for post in blog_posts}
    existing_files = {path.name for path in POSTS_DIR.glob("*.md")}

    if article_id in existing_ids:
        print(f"Ya existe un artículo con id: {article_id}")
        sys.exit(1)

    if markdown_filename in existing_files:
        print(f"Ya existe el archivo Markdown: {markdown_filename}")
        sys.exit(1)

    new_blog_entry = {
        "id": article_id,
        "fecha": fecha,
        "titulo": title,
        "extracto": excerpt,
        "cuerpo": body if isinstance(body, list) else [body],
        "etiqueta": tag
    }

    blog_posts.insert(0, new_blog_entry)

    BLOG_POSTS_FILE.write_text(
        json.dumps(blog_posts, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    markdown_content = build_markdown(
        article=article,
        article_id=article_id,
        title=title,
        date_iso=date_iso,
        fecha=fecha,
        tag=tag,
        excerpt=excerpt,
        body=body
    )

    markdown_path.write_text(markdown_content, encoding="utf-8")

    print("Artículo publicado correctamente.")
    print(f"Entrada añadida a: {BLOG_POSTS_FILE}")
    print(f"Markdown creado en: {markdown_path}")


if __name__ == "__main__":
    main()
