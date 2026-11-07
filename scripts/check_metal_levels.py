####
#List every MetalLevel value for individual-market medical plans, by year.

#Run from the project folder:  .venv\\Scripts\\python scripts\\check_metal_levels.py
#Reads data/raw/ only. Writes nothing.
###


import duckdb

duckdb.connect().sql("""
    SELECT BusinessYear AS yr, MetalLevel,
           count(DISTINCT StandardComponentId) AS plans
    FROM read_csv('data/raw/*/plan-attributes-puf.csv',
                  all_varchar = true, union_by_name = true)
    WHERE MarketCoverage = 'Individual' AND DentalOnlyPlan = 'No'
    GROUP BY ALL
    ORDER BY ALL
""").show(max_rows=50)