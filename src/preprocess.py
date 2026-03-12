import re


def clean_text(text):
    text = str(text)

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def preprocess_dataframe(df):

    df = df.copy()

    df["text"] = df["text"].apply(clean_text)

    df = df[df["text"].str.len() > 20]

    df = df.drop_duplicates(subset=["text"])

    return df