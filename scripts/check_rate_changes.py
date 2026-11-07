"""Step 5.2 check: the price changes behind the comparison.

Run from the project folder after dbt build:  .venv\\Scripts\\python scripts\\check_rate_changes.py
Reads the tables dbt built in aca_premiums.duckdb. Writes nothing.
"""
import duckdb

con = duckdb.connect("aca_premiums.duckdb", read_only=True)

print("Coverage")
con.sql("""
    select 'Plan pairs' as measure,
           (select count(*) from int_plan_pairs) as value
    union all
    select 'Pairs with at least one rating area priced in both years',
           (select count(distinct pair_key) from int_rate_changes)
    union all
    select 'Pairs with no rating area priced in both years',
           (select count(*) from int_plan_pairs
            where pair_key not in (select pair_key from int_rate_changes))
    union all
    select 'Price changes (pair + rating area)',
           (select count(*) from int_rate_changes)
""").show(max_width=120)

print("Spread of age-40 price changes (all pair + rating area rows)")
con.sql("""
    select round(min(change_pct) * 100, 1)                          as min_pct,
           round(quantile_cont(change_pct, 0.25) * 100, 1)          as p25_pct,
           round(median(change_pct) * 100, 1)                       as median_pct,
           round(quantile_cont(change_pct, 0.75) * 100, 1)          as p75_pct,
           round(max(change_pct) * 100, 1)                          as max_pct,
           count(*) filter (where change_pct < 0)                   as decreases,
           count(*) filter (where change_pct = 0)                   as no_change,
           count(*) filter (where abs(change_pct) > 0.5)            as moves_over_50pct
    from int_rate_changes
""").show(max_width=160)