"""Step 5.3 check: the final table's row count, merges, spread of
plan-level changes, and where the biggest rating-area increases come from.
Read-only. Run from the repo folder."""
import duckdb

FINAL = "data/clean/plan_premium_changes.parquet"
con = duckdb.connect("aca_premiums.duckdb", read_only=True)

rows, plans = con.execute(f"""
    select (select count(*) from '{FINAL}'),
           (select count(distinct plan_id_2027) from int_plan_pairs)
""").fetchone()
print(f"Rows in final table:            {rows:,}")
print(f"2027 plans in matched pairs:    {plans:,}")

print("\n2026 plans feeding each 2027 plan:")
for n, count in con.execute(f"""
    select predecessor_count, count(*) from '{FINAL}' group by 1 order by 1
""").fetchall():
    print(f"  {n}: {count:,} plans")

print("\nPlan-level change (average across rating areas):")
r = con.execute(f"""
    select min(avg_change_pct), quantile_cont(avg_change_pct, 0.25),
           median(avg_change_pct), quantile_cont(avg_change_pct, 0.75),
           max(avg_change_pct),
           count(*) filter (avg_change_pct < 0),
           count(*) filter (avg_change_pct > 0.5)
    from '{FINAL}'
""").fetchone()
for label, value in zip(["min", "p25", "median", "p75", "max"], r[:5]):
    print(f"  {label:7} {value:+.1%}")
print(f"  plans with a decrease:     {r[5]:,}")
print(f"  plans up more than 50%:    {r[6]:,}")

print("\nRating-area increases over 50%, by insurer and state:")
for state, issuer, n in con.execute("""
    select state, issuer_name, count(*)
    from int_rate_changes where change_pct > 0.5
    group by all order by 3 desc, 1, 2
""").fetchall():
    print(f"  {state}  {n:>4}  {issuer}")
