
from pathlib import Path
import requests
import zstandard
import shutil


BASE_DIR = Path(__file__).resolve().parent.parent
DEMOS_DIR = BASE_DIR / "demos"


def download_demo(demo_url, match_id):

    # Создаём папку для демо
    DEMOS_DIR.mkdir(exist_ok=True)

    # Пути к файлам
    compressed_path = DEMOS_DIR / f"{match_id}.dem.zst"
    demo_path = DEMOS_DIR / f"{match_id}.dem"

    print("\nDownloading demo...")

    # Скачиваем сжатое демо
    response = requests.get(demo_url, stream=True)
    response.raise_for_status()

    with open(compressed_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)

    print("Demo downloaded!")

    # Распаковываем демо
    print("Extracting demo...")

    with zstandard.open(compressed_path, "rb") as compressed_file:
        with open(demo_path, "wb") as demo_file:
            shutil.copyfileobj(compressed_file, demo_file)

    print("Demo extracted!")
    print("File:", demo_path)

    return demo_path
