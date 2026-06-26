import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ELA_FILE = ROOT / "ELA.html"


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def find_browser():
    candidates = []

    if os.environ.get("BROWSER_PATH"):
        candidates.append(Path(os.environ["BROWSER_PATH"]))

    program_files = [
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("LOCALAPPDATA"),
    ]

    for base in program_files:
        if not base:
            continue

        base_path = Path(base)
        candidates.extend([
            base_path / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            base_path / "Google" / "Chrome" / "Application" / "chrome.exe",
            base_path / "Chromium" / "Application" / "chrome.exe",
        ])

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def start_server():
    port = find_free_port()
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(
        *args,
        directory=str(ROOT),
        **kwargs
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{port}/ELA.html"


def request_status(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status


def run_screenshot(browser, url, width, height, output_path):
    with tempfile.TemporaryDirectory(prefix="ela-visual-profile-") as profile_dir:
        command = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--disable-gpu-compositing",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-features=UseSkiaRenderer,DawnGraphite,Vulkan",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={profile_dir}",
            "--hide-scrollbars",
            f"--window-size={width},{height}",
            f"--screenshot={output_path}",
            url,
        ]
        completed = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=40,
        )

    return {
        "exit_code": completed.returncode,
        "screenshot": str(output_path),
        "screenshot_exists": output_path.exists(),
        "screenshot_bytes": output_path.stat().st_size if output_path.exists() else 0,
        "stderr": completed.stderr.strip()[-500:],
    }


def static_page_checks():
    html = ELA_FILE.read_text(encoding="utf-8")

    return {
        "has_header": "<header" in html.lower(),
        "has_footer": "<footer" in html.lower(),
        "h1_count": html.lower().count("<h1"),
        "has_news_data": "const newsData" in html,
        "has_back_to_top_hook": "script.js" in html,
    }


def main():
    if not ELA_FILE.exists():
        raise FileNotFoundError("No se encontro ELA.html.")

    server, url = start_server()
    output_dir = ROOT / ".visual-checks"
    output_dir.mkdir(exist_ok=True)
    browser = find_browser()

    result = {
        "url": url,
        "http_status": None,
        "visual_status": "pending",
        "static": static_page_checks(),
        "browser": str(browser) if browser else None,
        "desktop": None,
        "mobile": None,
    }

    try:
        result["http_status"] = request_status(url)

        if browser:
            result["desktop"] = run_screenshot(
                browser,
                url,
                1365,
                900,
                output_dir / "ELA-desktop.png",
            )
            result["mobile"] = run_screenshot(
                browser,
                url,
                390,
                844,
                output_dir / "ELA-mobile.png",
            )
            desktop_ok = result["desktop"]["exit_code"] == 0 and result["desktop"]["screenshot_bytes"] > 10000
            mobile_ok = result["mobile"]["exit_code"] == 0 and result["mobile"]["screenshot_bytes"] > 10000
            result["visual_status"] = "ok" if desktop_ok and mobile_ok else "browser_failed"
        else:
            result["visual_status"] = "browser_not_found"
            result["browser_note"] = (
                "No se encontro Edge/Chrome. Define BROWSER_PATH para activar capturas visuales."
            )
    finally:
        server.shutdown()
        server.server_close()

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["http_status"] != 200:
        sys.exit(1)

    if browser and result["visual_status"] != "ok":
        sys.exit(1)


if __name__ == "__main__":
    main()
