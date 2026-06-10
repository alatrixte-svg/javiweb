from pathlib import Path
from PIL import Image, ImageOps

ASSETS_DIR = Path("assets")

MAX_WIDTH = 1600
MAX_HEIGHT = 1600

JPEG_QUALITY = 82
WEBP_QUALITY = 82
PNG_COMPRESS_LEVEL = 9

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def optimize_image(path: Path) -> bool:
    try:
        original_size = path.stat().st_size

        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)

            if img.mode in ("RGBA", "LA"):
                has_alpha = True
            else:
                has_alpha = False

            width, height = img.size

            if width > MAX_WIDTH or height > MAX_HEIGHT:
                img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

            suffix = path.suffix.lower()

            if suffix in [".jpg", ".jpeg"]:
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                img.save(
                    path,
                    format="JPEG",
                    quality=JPEG_QUALITY,
                    optimize=True,
                    progressive=True
                )

            elif suffix == ".png":
                if not has_alpha and img.mode != "P":
                    img = img.convert("RGB")

                img.save(
                    path,
                    format="PNG",
                    optimize=True,
                    compress_level=PNG_COMPRESS_LEVEL
                )

            elif suffix == ".webp":
                img.save(
                    path,
                    format="WEBP",
                    quality=WEBP_QUALITY,
                    method=6
                )

        new_size = path.stat().st_size

        if new_size < original_size:
            saved_kb = (original_size - new_size) / 1024
            print(f"Optimizada: {path} (-{saved_kb:.1f} KB)")
            return True

        print(f"Sin mejora: {path}")
        return False

    except Exception as error:
        print(f"Error optimizando {path}: {error}")
        return False


def main():
    if not ASSETS_DIR.exists():
        print("No existe la carpeta assets/")
        return

    changed = False

    for path in ASSETS_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            if optimize_image(path):
                changed = True

    if changed:
        print("Optimización completada con cambios.")
    else:
        print("No hubo imágenes que mejorar.")


if __name__ == "__main__":
    main()
