"""Profile the raw CMS files to answer the questions the data dictionaries can't.

Run from the project folder:  .venv\\Scripts\\python scripts\\profile_raw.py
Reads data/raw/ only. Writes nothing.
"""
import duckdb

con = duckdb.connect()

for name, path in {
    "rate26": "data/raw/2026/rate-puf.csv",
    "rate27": "data/raw/2027/rate-puf.csv",
    "plan26": "data/raw/2026/plan-attributes-puf.csv",
    "plan27": "data/raw/2027/plan-attributes-puf.csv",
    "xwalk": "data/raw/2027/plan-id-crosswalk-puf.csv",
}.items():
    con.execute(
        f"CREATE VIEW {name} AS SELECT * FROM read_csv('{path}', all_varchar = true)"
    )

con.execute("""
CREATE VIEW rates AS
    SELECT * FROM rate26 UNION ALL BY NAME SELECT * FROM rate27;
CREATE VIEW plans AS
    SELECT * FROM plan26 UNION ALL BY NAME SELECT * FROM plan27;
-- Plans in scope: individual market, medical, bronze/silver/gold (one row per plan)
CREATE VIEW scope AS
    SELECT DISTINCT BusinessYear, StateCode, IssuerId, StandardComponentId,
           MetalLevel, PlanType
    FROM plans
    WHERE MarketCoverage = 'Individual'
      AND DentalOnlyPlan = 'No'
      AND MetalLevel IN ('Bronze', 'Silver', 'Gold');
""")


def show(title, sql, rows=60):
    print(f"\n=== {title} ===")
    con.sql(sql).show(max_rows=rows, max_width=200)


show("1. Plan ID lengths", """
    SELECT 'rate PlanId' AS field, BusinessYear AS yr, length(PlanId) AS len, count(*) AS n
      FROM rates GROUP BY ALL
    UNION ALL
    SELECT 'plan StandardComponentId', BusinessYear, length(StandardComponentId), count(*)
      FROM plans GROUP BY ALL
    UNION ALL
    SELECT 'plan PlanId', BusinessYear, length(PlanId), count(*)
      FROM plans GROUP BY ALL
    UNION ALL
    SELECT 'xwalk PlanID_2026', '2027', length(PlanID_2026), count(*)
      FROM xwalk GROUP BY ALL
    UNION ALL
    SELECT 'xwalk PlanID_2027', '2027', length(PlanID_2027), count(*)
      FROM xwalk GROUP BY ALL
    ORDER BY ALL
""")

show("2. Variant suffix vs CSR type (2027, individual medical plans)", """
    SELECT split_part(PlanId, '-', 2) AS suffix, CSRVariationType, count(*) AS n
    FROM plan27
    WHERE MarketCoverage = 'Individual' AND DentalOnlyPlan = 'No'
    GROUP BY ALL ORDER BY suffix, n DESC
""")

show("3. Plans whose attributes differ across their variants (should all be 0)", """
    SELECT BusinessYear AS yr,
           count(*) FILTER (WHERE metals > 1)  AS metal_differs,
           count(*) FILTER (WHERE types > 1)   AS plan_type_differs,
           count(*) FILTER (WHERE markets > 1) AS market_differs,
           count(*) FILTER (WHERE issuers > 1) AS issuer_differs
    FROM (
        SELECT BusinessYear, StandardComponentId,
               count(DISTINCT MetalLevel) AS metals,
               count(DISTINCT PlanType) AS types,
               count(DISTINCT MarketCoverage) AS markets,
               count(DISTINCT IssuerId) AS issuers
        FROM plans GROUP BY ALL
    ) GROUP BY ALL ORDER BY ALL
""")

show("4. In-scope plans by year, metal level and plan type", """
    SELECT BusinessYear AS yr, MetalLevel, PlanType, count(*) AS plans
    FROM scope GROUP BY ALL ORDER BY ALL
""")

show("5. States with in-scope plans in only one year", """
    WITH s AS (SELECT DISTINCT BusinessYear, StateCode FROM scope)
    SELECT StateCode, list(BusinessYear ORDER BY BusinessYear) AS years
    FROM s GROUP BY ALL HAVING count(*) = 1 ORDER BY ALL
""")
show("5b. State count per year", """
    SELECT BusinessYear AS yr, count(DISTINCT StateCode) AS states
    FROM scope GROUP BY ALL ORDER BY ALL
""")

show("6. Join coverage: in-scope plans with no rate rows", """
    SELECT s.BusinessYear AS yr, count(*) AS plans_without_rates
    FROM scope s
    LEFT JOIN (SELECT DISTINCT BusinessYear, PlanId FROM rates) r
      ON r.BusinessYear = s.BusinessYear AND r.PlanId = s.StandardComponentId
    WHERE r.PlanId IS NULL
    GROUP BY ALL ORDER BY ALL
""")

show("7. Age-40 rate vs Family Option (in-scope plans)", """
    WITH p AS (
        SELECT s.BusinessYear, s.StandardComponentId, s.StateCode,
               bool_or(r.Age = '40') AS has_age40,
               bool_or(r.Age = 'Family Option') AS has_family
        FROM scope s
        JOIN rates r ON r.BusinessYear = s.BusinessYear AND r.PlanId = s.StandardComponentId
        GROUP BY ALL
    )
    SELECT BusinessYear AS yr, has_age40, has_family, count(*) AS plans,
           list(DISTINCT StateCode ORDER BY StateCode) AS states
    FROM p GROUP BY ALL ORDER BY ALL
""")

show("8. Rating areas per in-scope plan (age 40)", """
    WITH a AS (
        SELECT r.BusinessYear, r.PlanId, count(DISTINCT r.RatingAreaId) AS areas
        FROM rates r
        JOIN (SELECT DISTINCT BusinessYear, StandardComponentId FROM scope) s
          ON s.BusinessYear = r.BusinessYear AND s.StandardComponentId = r.PlanId
        WHERE r.Age = '40'
        GROUP BY ALL
    )
    SELECT BusinessYear AS yr, min(areas) AS min_areas, median(areas) AS median_areas,
           max(areas) AS max_areas, count(*) AS plans
    FROM a GROUP BY ALL ORDER BY ALL
""")

show("9. Age-40 rows per plan + rating area (1 = clean; more = duplicates to resolve)", """
    WITH d AS (
        SELECT r.BusinessYear, r.PlanId, r.RatingAreaId,
               count(*) AS rows_, count(DISTINCT r.RateEffectiveDate) AS eff_dates,
               count(*) FILTER (WHERE try_cast(r.IndividualRate AS DOUBLE) IS NULL) AS bad_rates
        FROM rates r
        JOIN (SELECT DISTINCT BusinessYear, StandardComponentId FROM scope) s
          ON s.BusinessYear = r.BusinessYear AND s.StandardComponentId = r.PlanId
        WHERE r.Age = '40'
        GROUP BY ALL
    )
    SELECT BusinessYear AS yr, rows_ AS rows_per_combo, eff_dates,
           count(*) AS combos, sum(bad_rates) AS non_numeric_rates
    FROM d GROUP BY ALL ORDER BY ALL
""")

show("10. Crosswalk reasons and levels (medical plans only)", """
    SELECT ReasonForCrosswalk AS reason, CrosswalkLevel AS level, count(*) AS rows_,
           count(DISTINCT PlanID_2026) AS plans_2026
    FROM xwalk WHERE DentalPlan = 'N'
    GROUP BY ALL ORDER BY ALL
""")

show("11. 2026 plans that map to more than one 2027 plan (medical)", """
    WITH m AS (
        SELECT PlanID_2026, count(DISTINCT PlanID_2027) AS targets
        FROM xwalk WHERE DentalPlan = 'N' AND PlanID_2027 IS NOT NULL
        GROUP BY ALL
    )
    SELECT targets AS distinct_2027_plans, count(*) AS plans_2026
    FROM m GROUP BY ALL ORDER BY ALL
""")