# Print the row count of every raw CMS CSV in data/raw/
from pathlib import Path

import duckdb

files = sorted(Path("data/raw").glob("*/*.csv"))
if not files:
    raise SystemExit("No CSV files found in data/raw/<year>/")

con = duckdb.connect()
for f in files:
    rows = con.execute(
        f"SELECT count(*) FROM read_csv('{f.as_posix()}', all_varchar = true)"
    ).fetchone()[0]
    print(f"{f.as_posix():<60} {rows:>12,} rows")