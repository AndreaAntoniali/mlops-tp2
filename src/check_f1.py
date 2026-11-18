"""Cycle 4: fail the CI when the model is too weak.

    python src/check_f1.py

Reads metrics.json, written by the evaluate stage. A CI step that exits with a
non-zero code turns the whole job red.
"""
import json
import sys

THRESHOLD = 0.75   # the TP model scores about 0.76

##### cycle 4, etape 4 : lisez le f1 dans metrics.json (json.load)
f1 = None

print(f"f1 = {f1}  (threshold {THRESHOLD})")

##### cycle 4, etape 4 : sortez avec le code 0 si f1 >= THRESHOLD, 1 sinon (sys.exit)
