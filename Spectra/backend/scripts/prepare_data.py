import io
import ssl
import urllib.request
import zipfile
from pathlib import Path
import certifi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = PROJECT_ROOT / "datasets" / "ml-1m"
URL = "https://files.grouplens.org/datasets/movielens/ml-1m.zip"

def main():
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    required = ["movies.dat", "ratings.dat", "users.dat"]
    if all((DATASET_DIR / name).exists() for name in required):
        print(f"MovieLens 1M already exists: {DATASET_DIR}")
        return
    print("Downloading MovieLens 1M...")
    request = urllib.request.Request(URL, headers={"User-Agent": "Spectra/1.0"})
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(request, timeout=120, context=context) as response:
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in required:
            with archive.open(f"ml-1m/{name}") as source:
                (DATASET_DIR / name).write_bytes(source.read())
    print(f"Dataset ready: {DATASET_DIR}")

if __name__ == "__main__":
    main()
