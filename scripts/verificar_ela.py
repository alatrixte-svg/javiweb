import argparse
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ELA_FILE = ROOT / "ELA.html"
CANDIDATE_FILE = ROOT / "candidate-news.json"
BACKUP_FILE = ROOT / "candidate-news.backup.json"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = set()
        self.links = []
        self.images = []
        self.h1_count = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.tags.append(tag)

        if "id" in attrs_dict:
            self.ids.add(attrs_dict["id"])

        if tag == "a" and attrs_dict.get("href"):
            self.links.append(attrs_dict["href"])

        if tag == "img":
            self.images.append(attrs_dict)

        if tag == "h1":
            self.h1_count += 1


def load_json(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    news = data.get("news", [])
    total = data.get("total")
    return data, total == len(news), len(news)


def parse_html(path):
    html = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)
    return html, parser


def find_missing_internal_links(parser):
    missing = []

    for href in parser.links:
        if href.startswith(("http://", "https://", "mailto:", "tel:")):
            continue

        if href.startswith("#"):
            if href[1:] and href[1:] not in parser.ids:
                missing.append(href)
            continue

        parsed = urlparse(href)
        target_path = parsed.path
        target_fragment = parsed.fragment

        if not target_path:
            target_file = ELA_FILE
        else:
            target_file = ROOT / target_path

        if target_path and not target_file.exists():
            missing.append(href)
            continue

        if target_fragment:
            target_html = target_file.read_text(encoding="utf-8")
            target_parser = PageParser()
            target_parser.feed(target_html)

            if target_fragment not in target_parser.ids:
                missing.append(href)

    return missing


def extract_news_links(html):
    return re.findall(
        r'link:\s*"(?P<link>https?://[^"]+)"',
        html,
    )


def check_news_links(links):
    status_counts = {}

    for link in links:
        try:
            request = urllib.request.Request(
                link,
                headers={"User-Agent": "Mozilla/5.0 ELA Link Check"},
            )

            with urllib.request.urlopen(request, timeout=10) as response:
                key = str(response.status)
        except Exception as error:
            key = type(error).__name__

        status_counts[key] = status_counts.get(key, 0) + 1

    return status_counts


def main():
    arg_parser = argparse.ArgumentParser(
        description="Verifica los archivos principales del flujo de noticias ELA."
    )
    arg_parser.add_argument(
        "--check-news-links",
        action="store_true",
        help="Comprueba por red los enlaces generados en newsData.",
    )
    args = arg_parser.parse_args()

    errors = []

    candidate_data, candidate_total_ok, candidate_count = load_json(CANDIDATE_FILE)
    backup_data, backup_total_ok, backup_count = load_json(BACKUP_FILE)
    html, page = parse_html(ELA_FILE)
    news_links = extract_news_links(html)
    missing_internal_links = find_missing_internal_links(page)

    checks = {
        "candidate_total": candidate_data.get("total"),
        "candidate_items": candidate_count,
        "candidate_total_ok": candidate_total_ok,
        "backup_total": backup_data.get("total"),
        "backup_items": backup_count,
        "backup_total_ok": backup_total_ok,
        "has_newsData": bool(re.search(r"const\s+newsData\s*=\s*\[", html)),
        "newsData_links": len(news_links),
        "h1_count": page.h1_count,
        "has_header": "header" in page.tags,
        "has_footer": "footer" in page.tags,
        "images": len(page.images),
        "images_without_alt": sum(1 for image in page.images if not image.get("alt")),
        "internal_missing": missing_internal_links,
    }

    if args.check_news_links:
        checks["news_link_status_counts"] = check_news_links(news_links)

    if not candidate_total_ok:
        errors.append("candidate-news.json tiene un total que no coincide.")

    if not backup_total_ok:
        errors.append("candidate-news.backup.json tiene un total que no coincide.")

    if not checks["has_newsData"]:
        errors.append("ELA.html no contiene newsData.")

    if page.h1_count != 1:
        errors.append("ELA.html debe tener exactamente un h1.")

    if "header" not in page.tags:
        errors.append("ELA.html no contiene header semantico.")

    if "footer" not in page.tags:
        errors.append("ELA.html no contiene footer semantico.")

    if checks["images_without_alt"]:
        errors.append("Hay imagenes sin alt.")

    if missing_internal_links:
        errors.append("Hay enlaces internos que no resuelven.")

    print(json.dumps(checks, ensure_ascii=False, indent=2))

    if errors:
        print("\nErrores:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    print("\nVerificacion correcta.")


if __name__ == "__main__":
    main()
