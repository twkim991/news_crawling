import os

DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
OUTPUT_DIR = "outputs"
MODELS_DIR = "models"

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"
DEFAULT_BINARY_MODEL_PATH = os.path.join(MODELS_DIR, "ag_binary_logreg.joblib")
DEFAULT_TECH_THRESHOLD = 0.55
DEFAULT_UNCERTAINTY_MARGIN = 0.08

NEWSAPI_RAW_PATH = os.path.join(RAW_DIR, "newsapi_raw.csv")
NEWSAPI_PROCESSED_PATH = os.path.join(PROCESSED_DIR, "newsapi_processed.csv")
GDELT_RAW_PATH = os.path.join(RAW_DIR, "gdelt_raw_gkg.csv")
GDELT_PROCESSED_PATH = os.path.join(PROCESSED_DIR, "gdelt_processed.csv")

AG_TRAIN_PATH = os.path.join(RAW_DIR, "train.csv")
AG_TEST_PATH = os.path.join(RAW_DIR, "test.csv")
AG_TRAIN_EMB_PATH = os.path.join(MODELS_DIR, "ag_train_embeddings.npy")
AG_TEST_EMB_PATH = os.path.join(MODELS_DIR, "ag_test_embeddings.npy")
