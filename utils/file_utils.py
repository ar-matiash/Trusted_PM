from pathlib import Path


def ensure_storage_folder():

    path = Path("storage")

    if not path.exists():
        path.mkdir()