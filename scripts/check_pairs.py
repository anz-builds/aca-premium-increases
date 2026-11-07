"""Step 5.1 check: how 2026 plans matched to 2027 plans.

Run from the project folder after dbt build:  .venv\\Scripts\\python scripts\\check_pairs.py
Reads the tables dbt built in aca_premiums.duckdb. Writes nothing.
"""
import duckdb

con = duckdb.connect("aca_premiums.duckdb", read_only=True)
con.sql("""
    with pairs as (select * from int_plan_pairs),
         plans_2026 as (select * from int_scope_plans where plan_year = 2026)

    select 'Pairs from reason 0 (same plan ID)' as measure,
           count(*) filter (where crosswalk_reason = 0) as value from pairs
    union all
    select 'Pairs from reason 1 (same plan, new ID)',
           count(*) filter (where crosswalk_reason = 1) from pairs
    union all
    select '2026 plans with 2+ pairs (split)',
           count(*) from (select plan_id_2026 from pairs group by all having count(*) > 1)
    union all
    select '2027 plans with 2+ 2026 plans (merged)',
           count(*) from (select plan_id_2027 from pairs group by all having count(*) > 1)
    union all
    select 'Pairs where metal level changed',
           count(*) filter (where metal_level <> metal_level_2026) from pairs
    union all
    select 'Pairs where plan type changed',
           count(*) filter (where plan_type <> plan_type_2026) from pairs
    union all
    select 'Pairs where insurer changed',
           count(*) filter (where issuer_id <> issuer_id_2026) from pairs
    union all
    select 'In-scope 2026 plans with no pair',
           count(*) from plans_2026
           where plan_id not in (select plan_id_2026 from pairs)
""").show(max_width=120)
