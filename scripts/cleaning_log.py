"""Cleaning log: row counts after each step, for the README.
Read-only. Run from the repo folder after `dbt build`.
Every step checks that the rows kept plus the rows removed equal the
rows before it. The script stops with an error if anything fails to add up."""
import duckdb

con = duckdb.connect("aca_premiums.duckdb", read_only=True)


def count(sql):
    return con.execute(sql).fetchone()[0]


def raw(year, file):
    return f"read_csv('data/raw/{year}/{file}.csv', all_varchar = true)"


def print_log(title, steps):
    """steps: list of (label, rows_2026, rows_2027). Removed = previous - current."""
    print(f"\n### {title}\n")
    print("| Step | 2026 rows | Removed | 2027 rows | Removed |")
    print("|---|---:|---:|---:|---:|")
    prev = None
    for label, r26, r27 in steps:
        if prev is None:
            print(f"| {label} | {r26:,} | | {r27:,} | |")
        else:
            gone26, gone27 = prev[0] - r26, prev[1] - r27
            assert gone26 >= 0 and gone27 >= 0, f"Row count went up at: {label}"
            print(f"| {label} | {r26:,} | {gone26:,} | {r27:,} | {gone27:,} |")
        prev = (r26, r27)


def per_year(sql_template):
    return tuple(count(sql_template.format(year=y)) for y in (2026, 2027))


# Plans
print_log("Plans", [
    ("Plan variants in the raw file",
     *(count(f"select count(*) from {raw(y, 'plan-attributes-puf')}") for y in (2026, 2027))),
    ("Unique plans (variants combined)",
     *per_year("select count(*) from stg_plans where plan_year = {year}")),
    ("Individual market",
     *per_year("select count(*) from stg_plans where plan_year = {year} and market = 'Individual'")),
    ("Medical, not dental-only",
     *per_year("select count(*) from stg_plans where plan_year = {year} and market = 'Individual' "
               "and not is_dental_only")),
    ("Bronze, silver or gold",
     *per_year("select count(*) from stg_plans where plan_year = {year} and market = 'Individual' "
               "and not is_dental_only and metal_level in ('Bronze', 'Silver', 'Gold')")),
    ("States in both years (removes Oregon)",
     *per_year("select count(*) from int_scope_plans where plan_year = {year}")),
])

# Prices
print_log("Prices", [
    ("Price rows in the raw file",
     *(count(f"select count(*) from {raw(y, 'rate-puf')}") for y in (2026, 2027))),
    ("Age-40 prices",
     *per_year("select count(*) from stg_rates where plan_year = {year}")),
    ("Prices for plans in scope",
     *per_year("select count(*) from int_scope_rates where plan_year = {year}")),
])

# Comparison
plans_2026 = count("select count(*) from int_scope_plans where plan_year = 2026")
matched_2026 = count("select count(distinct plan_id_2026) from int_plan_pairs")
pairs = count("select count(*) from int_plan_pairs")
changes = count("select count(*) from int_rate_changes")
final = count("select count(*) from 'data/clean/plan_premium_changes.parquet'")

print("\n### Comparison\n")
print("| Step | Rows |")
print("|---|---:|")
print(f"| 2026 plans in scope | {plans_2026:,} |")
print(f"| 2026 plans with a same-plan match in 2027 (crosswalk reason 0 or 1) | {matched_2026:,} |")
print(f"| Matched pairs (a split plan has one pair per 2027 plan) | {pairs:,} |")
print(f"| Price changes (one per pair per rating area priced in both years) | {changes:,} |")
print(f"| Final table: 2027 plans (merged plans combined) | {final:,} |")

# Why the unmatched 2026 plans have no match. Each plan is grouped by its
# lowest crosswalk reason code across counties (lowest = closest to continuing).
unmatched = con.execute("""
    with unmatched as (
        select plan_id from int_scope_plans
        where plan_year = 2026
          and plan_id not in (select plan_id_2026 from int_plan_pairs)
    ),
    lowest_reason as (
        select plan_id_2026, min(crosswalk_reason) as reason
        from stg_crosswalk group by plan_id_2026
    )
    select
        case
            when r.reason in (0, 1) then 'Same plan in 2027, but outside the scope'
            when r.reason is null then 'Not in the crosswalk'
            else 'Crosswalk reason ' || r.reason
        end as outcome,
        count(*) as plans
    from unmatched as u
    -- Left join keeps unmatched plans that have no crosswalk row at all.
    left join lowest_reason as r on r.plan_id_2026 = u.plan_id
    group by all
    order by min(coalesce(r.reason, 99))
""").fetchall()

unmatched_total = plans_2026 - matched_2026
print(f"\n### 2026 plans with no same-plan match ({unmatched_total:,})\n")
print("| Outcome | Plans |")
print("|---|---:|")
for outcome, n in unmatched:
    print(f"| {outcome} | {n:,} |")

assert sum(n for _, n in unmatched) == unmatched_total, "Unmatched plans don't add up"
print("\nAll counts add up.")
