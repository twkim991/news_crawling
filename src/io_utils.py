import os


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
