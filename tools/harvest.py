#!/usr/bin/env python
"""Write the batch of wines that arrived "today" into data/current.csv.

    python tools/harvest.py              an honest batch -- nothing has changed
    python tools/harvest.py --warm       a warmer harvest (traffic.py --drift)
    python tools/harvest.py --cellar     a cellar that uses more sulfites
    python tools/harvest.py --n 50       keep only 50 wines of that batch

Nothing here is corrupt: every wine stays plausible, and every value stays
inside the bounds of src/schema.py. These wines are simply not the wines the
model learned on, which is what happens to any model left in production.

The batch is the test set, so the wines are real ones the model never saw.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

TEST = Path("data/prepared/test.csv")
OUT = Path("data/current.csv")

# A warmer year: more alcohol, slightly less acidity, lighter wines.
# Exactly the shift tools/traffic.py --drift sends to the API.
WARM = {"alcohol": +0.7, "volatile acidity": -0.15, "density": -0.0014}

# A cellar that sulfites more, and salts its must a little. Three columns
# a warmer year does not move.
CELLAR = {"total sulfur dioxide": +25, "free sulfur dioxide": +8, "chlorides": +0.02}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--warm", action="store_true")
    parser.add_argument("--cellar", action="store_true")
    parser.add_argument("--n", type=int, default=0, help="keep only N wines")
    args = parser.parse_args()

    if not TEST.exists():
        sys.exit(f"{TEST} is missing. Run the pipeline first:    dvc repro")

    wines = pd.read_csv(TEST).drop(columns=["good"])

    shift, label = {}, "an honest batch"
    if args.warm:
        shift, label = WARM, "a warmer harvest"
    elif args.cellar:
        shift, label = CELLAR, "a cellar that uses more sulfites"

    for column, delta in shift.items():
        wines[column] = wines[column] + delta

    if args.n:
        # No replacement: drawing the same wine twice would deform the batch
        # all by itself. See the question of cycle 6.
        wines = wines.sample(n=min(args.n, len(wines)), random_state=0)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wines.to_csv(OUT, index=False)
    print(f"{OUT}: {len(wines)} wines -- {label}")
    if shift:
        print("  " + ", ".join(f"{c} {d:+}" for c, d in shift.items()))


if __name__ == "__main__":
    main()
