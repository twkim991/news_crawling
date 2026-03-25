# ssafy_dataset_analysis_pipeline.py

import argparse
import os

from src.gdelt_analysis_pipeline import run_gdelt_analysis

INPUT_PATH = os.path.join("data", "processed", "ssafy_dataset_processed.csv")
OUTPUT_DIR = "outputs"


def run_ssafy_dataset_analysis(
    input_path,
    output_dir,
    output_prefix="ssafy_dataset",
):
    return run_gdelt_analysis(
        input_path=input_path,
        output_dir=output_dir,
        output_prefix=output_prefix,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze processed SSAFY dataset data and build stack trend scores"
    )
    parser.add_argument(
        "--input-path",
        default=INPUT_PATH,
        help="processed SSAFY dataset csv path",
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help="directory to save analysis outputs",
    )
    parser.add_argument(
        "--output-prefix",
        default="ssafy_dataset",
        help="prefix for output file names",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("[SSAFY Dataset Analysis] input_path :", args.input_path)
    print("[SSAFY Dataset Analysis] output_dir :", args.output_dir)
    print("[SSAFY Dataset Analysis] output_prefix :", args.output_prefix)

    run_ssafy_dataset_analysis(
        input_path=args.input_path,
        output_dir=args.output_dir,
        output_prefix=args.output_prefix,
    )


if __name__ == "__main__":
    main()