import os
import sys
import urllib.request
import zipfile

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip"
TARGET_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(TARGET_DIR, "model")
ARCHIVE_PATH = os.path.join(TARGET_DIR, "model.zip")

def download_and_extract():
    if os.path.exists(MODEL_DIR) and os.listdir(MODEL_DIR):
        print(f"[OK] Модель уже скачана: {MODEL_DIR}")
        return

    print(f"[i] Скачиваем русскую модель Vosk (~45MB) с {MODEL_URL}...")
    def reporthook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write(f"\rСкачано: {percent}%")
        sys.stdout.flush()

    urllib.request.urlretrieve(MODEL_URL, ARCHIVE_PATH, reporthook)
    print("\n[i] Распаковка архива...")
    with zipfile.ZipFile(ARCHIVE_PATH, "r") as zip_ref:
        zip_ref.extractall(TARGET_DIR)

    # Переименовываем папку 'vosk-model-small-ru-0.22' в 'model'
    extracted_folder = os.path.join(TARGET_DIR, "vosk-model-small-ru-0.22")
    if os.path.exists(extracted_folder):
        if os.path.exists(MODEL_DIR):
            import shutil
            shutil.rmtree(MODEL_DIR)
        os.rename(extracted_folder, MODEL_DIR)

    if os.path.exists(ARCHIVE_PATH):
        os.remove(ARCHIVE_PATH)
    print(f"[OK] Модель готова к работе в: {MODEL_DIR}")

if __name__ == "__main__":
    download_and_extract()
