-- Plans in scope: individual market, medical, bronze/silver/gold,
-- in states that have in-scope plans in both 2026 and 2027.
-- One row per plan per year.

with scope as (
    select *
    from {{ ref('stg_plans') }}
    where market = 'Individual'
      and not is_dental_only
      and metal_level in ('Bronze', 'Silver', 'Gold')
),

states_in_both_years as (
    select state
    from scope
    group by state
    having count(distinct plan_year) = 2
)

select scope.*
from scope
-- Inner join keeps only states present in both years (drops Oregon,
-- which left HealthCare.gov for 2027).
join states_in_both_years using (state)