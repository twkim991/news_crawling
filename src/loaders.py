import pandas as pd


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

    return df


def load_newsapi(path):
    df = pd.read_csv(path)

    df["source"] = "NewsAPI"

    df["title"] = df["title"].fillna("")
    df["description"] = df["description"].fillna("")
    df["content"] = df["content"].fillna("")

    df["text"] = df["title"] + ". " + df["description"]

    return df