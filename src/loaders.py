import pandas as pd

from common import ensure_schema


LABEL_MAP = {
    1: "World",
    2: "Sports",
    3: "Business",
    4: "Sci/Tech",
}


def load_ag_news(path):
    df = pd.read_csv(
        path,
        header=None,
        names=["class_index", "title", "description"]
    )

    df["content"] = ""
    df["url"] = ""
    df["published_at"] = ""
    df["source"] = "AG"

    df["text"] = df["title"].astype(str) + ". " + df["description"].astype(str)

    return ensure_schema(df, source_name="AG")


def load_newsapi(path):
    df = pd.read_csv(path)
    df = ensure_schema(df, source_name="NewsAPI")

    df["title"] = df["title"].fillna("")
    df["description"] = df["description"].fillna("")
    df["content"] = df["content"].fillna("")

    df["text"] = df["title"] + ". " + df["description"]

    return df


def load_gdelt(path):
    df = pd.read_csv(path)
    df = ensure_schema(df, source_name="GDELT")

    df["title"] = df["title"].fillna("")
    df["description"] = df["description"].fillna("")
    df["content"] = df["content"].fillna("")

    df["text"] = df["title"] + ". " + df["description"] + ". " + df["content"]

    return df


def load_ssafy_processed(path):
    df = pd.read_csv(path)
    df = ensure_schema(df)
    df["source"] = df["source"].fillna("").replace("", "SSAFY")
    return df
