#!/usr/bin/env python
"""Send wines to the running API, and say what it answered.

    python tools/traffic.py --n 1                    one wine, and the answer
    python tools/traffic.py --n 1 --set alcohol=45   the same wine, at 45% alcohol
    python tools/traffic.py                          400 wines from the test set
    python tools/traffic.py --drift                  wines from a warmer harvest

--drift does not corrupt anything: the wines stay plausible. They are simply
not the wines the model was trained on, which is exactly what happens to a
model left in production for a year. --set, on the other hand, can send a wine
no cellar has ever made.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import requests

TEST = Path("data/prepared/test.csv")
URL = "http://127.0.0.1:8000/predict"

# A warmer year: more alcohol, slightly less acidity, lighter wines.
DRIFT = {"alcohol": +0.7, "volatile acidity": -0.15, "density": -0.0014}


def setting(text):
    """'alcohol=45' -> ('alcohol', 45.0)"""
    column, _, value = text.partition("=")
    try:
        return column, float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected COLUMN=NUMBER, got {text!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=400)
    parser.add_argument("--drift", action="store_true")
    parser.add_argument(
        "--set", type=setting, action="append", default=[], metavar="COLUMN=VALUE",
        help="force one column to a value, in every wine sent",
    )
    parser.add_argument("--url", default=URL)
    args = parser.parse_args()

    if not TEST.exists():
        sys.exit(f"{TEST} is missing. Run the pipeline first:    dvc repro")

    df = pd.read_csv(TEST).drop(columns=["good"])
    wines = df.sample(n=args.n, replace=True, random_state=0).reset_index(drop=True)

    if args.drift:
        for column, shift in DRIFT.items():
            wines[column] = wines[column] + shift
    for column, value in args.set:
        if column not in wines.columns:
            sys.exit(f"no column named {column!r}. The columns: {', '.join(wines.columns)}")
        wines[column] = value

    what = "wine" if args.n == 1 else "wines"
    if args.drift:
        what += " from a warmer harvest"
    if args.set:
        what += ", with " + ", ".join(f"{c} = {v:g}" for c, v in args.set)
    print(f"sending {args.n} {what}")

    good = refused = 0
    for _, wine in wines.iterrows():
        try:
            answer = requests.post(args.url, json=wine.to_dict(), timeout=5)
        except requests.exceptions.ConnectionError:
            sys.exit(
                f"nothing is listening on {args.url}.\n"
                "Start the API first:    uvicorn src.serve:app"
            )
        if args.n == 1:
            print(f"<- {answer.status_code} {json.dumps(answer.json())}")
        if answer.status_code == 422:
            refused += 1
            continue
        answer.raise_for_status()
        good += answer.json()["good"]

    if args.n == 1:
        return
    served = args.n - refused
    if served:
        print(f"{good} of {served} predicted good ({100 * good / served:.0f}%)")
    if refused:
        print(f"{refused} of {args.n} refused by the API")
    print("now reload http://127.0.0.1:8000/metrics")


if __name__ == "__main__":
    main()
