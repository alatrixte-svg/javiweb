from pathlib import Path
from PIL import Image

ASSETS_DIR = Path("assets")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

MAX_WIDTH = 1800
JPEG_QUALITY = 85
WEBP_QUALITY = 85


def optimize_image(path: Path) -> None:
    try:
        with Image.open(path) as img:
            original_format = img.format
            img = img.convert("RGB") if img.mode in ("RGBA", "P") and path.suffix.lower() in {".jpg", ".jpeg"} else img

            if img.width > MAX_WIDTH:
                ratio = MAX_WIDTH / img.width
                new_height = int(img.height * ratio)
                img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

            save_kwargs = {}

            if path.suffix.lower() in {".jpg", ".jpeg"}:
                save_kwargs = {
                    "quality": JPEG_QUALITY,
                    "optimize": True,
                    "progressive": True,
                }
            elif path.suffix.lower() == ".png":
                save_kwargs = {
                    "optimize": True,
                }
            elif path.suffix.lower() == ".webp":
                save_kwargs = {
                    "quality": WEBP_QUALITY,
                    "method": 6,
                }

            img.save(path, format=original_format, **save_kwargs)
            print(f"Optimizada: {path}")

    except Exception as error:
        print(f"No se pudo optimizar {path}: {error}")


def main() -> None:
    if not ASSETS_DIR.exists():
        print("No existe la carpeta assets/")
        return

    images = [
        path for path in ASSETS_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]

    if not images:
        print("No se encontraron imágenes para optimizar.")
        return

    for image_path in images:
        optimize_image(image_path)


if __name__ == "__main__":
    main()
