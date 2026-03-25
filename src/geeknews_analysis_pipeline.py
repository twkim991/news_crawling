import argparse
import os

from src.gdelt_analysis_pipeline import run_gdelt_analysis

INPUT_PATH = os.path.join("data", "processed", "geeknews_processed.csv")
OUTPUT_DIR = "outputs"


def run_geeknews_analysis(
    input_path,
    output_dir,
    output_prefix="geeknews",
):
    return run_gdelt_analysis(
        input_path=input_path,
        output_dir=output_dir,
        output_prefix=output_prefix,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze processed GeekNews data and build stack trend scores"
    )
    parser.add_argument(
        "--input-path",
        default=INPUT_PATH,
        help="processed GeekNews csv path",
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        help="directory to save analysis outputs",
    )
    parser.add_argument(
        "--output-prefix",
        default="geeknews",
        help="prefix for output file names",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("[GeekNews Analysis] input_path :", args.input_path)
    print("[GeekNews Analysis] output_dir :", args.output_dir)
    print("[GeekNews Analysis] output_prefix :", args.output_prefix)

    run_geeknews_analysis(
        input_path=args.input_path,
        output_dir=args.output_dir,
        output_prefix=args.output_prefix,
    )


if __name__ == "__main__":
    main()