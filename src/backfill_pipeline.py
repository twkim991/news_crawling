import argparse
from datetime import datetime, timedelta

from src.pipeline import run_daily_pipeline


def daterange(start_date: datetime, end_date: datetime):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser(description="Run daily pipeline for a date range")
    parser.add_argument("--start-date", required=True, help="start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="end date (YYYY-MM-DD)")
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="continue even if one day fails",
    )
    args = parser.parse_args()

    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(args.end_date, "%Y-%m-%d")

    if start_dt > end_dt:
        raise ValueError("start-date must be earlier than or equal to end-date")

    total_days = (end_dt - start_dt).days + 1
    print("======================================")
    print(" BACKFILL PIPELINE START ")
    print(" start_date:", args.start_date)
    print(" end_date  :", args.end_date)
    print(" total_days:", total_days)
    print("======================================")

    success_count = 0
    failed_dates = []

    for idx, current_dt in enumerate(daterange(start_dt, end_dt), start=1):
        run_date = current_dt.strftime("%Y-%m-%d")
        print(f"\n[{idx}/{total_days}] RUN DATE: {run_date}")

        try:
            run_daily_pipeline(run_date)
            success_count += 1
        except Exception as e:
            print(f"[FAILED] {run_date} -> {e}")
            failed_dates.append(run_date)

            if not args.skip_errors:
                print("\nSTOPPED DUE TO ERROR")
                break

    print("\n======================================")
    print(" BACKFILL PIPELINE DONE ")
    print(" success_count:", success_count)
    print(" failed_count :", len(failed_dates))
    if failed_dates:
        print(" failed_dates :", ", ".join(failed_dates))
    print("======================================")


if __name__ == "__main__":
    main()