-- Final table for Power BI. Grain: one row per 2027 plan that continues
-- one or more 2026 plans.
-- Rule 2: a plan's change is the average of its rating-area changes, using
-- only rating areas priced in both years (age 40, non-tobacco).
-- Merged plans: where two or more 2026 plans became one 2027 plan, the
-- 2026 price in each rating area is the average of their prices.
{{ config(
    materialized = 'external',
    location = 'data/clean/plan_premium_changes.parquet'
) }}

with rate_changes as (
    select * from {{ ref('int_rate_changes') }}
),

plans_2027 as (
    select * from {{ ref('int_scope_plans') }} where plan_year = 2027
),

-- One row per 2027 plan and rating area; merged 2026 prices averaged.
area_prices as (
    select
        plan_id_2027,
        rating_area,
        avg(rate_2026)       as rate_2026,
        any_value(rate_2027) as rate_2027  -- one 2027 price per plan and area
    from rate_changes
    group by plan_id_2027, rating_area
),

-- One row per 2027 plan: Rule 2 average across its rating areas.
plan_changes as (
    select
        plan_id_2027,
        count(*)                                  as rating_area_count,
        avg(rate_2026)                            as avg_rate_2026,
        avg(rate_2027)                            as avg_rate_2027,
        avg(rate_2027 - rate_2026)                as avg_change_dollars,
        -- Stored as a fraction: 0.05 means a 5% increase
        avg((rate_2027 - rate_2026) / rate_2026)  as avg_change_pct
    from area_prices
    group by plan_id_2027
),

predecessors as (
    select
        plan_id_2027,
        count(distinct plan_id_2026)                                 as predecessor_count,
        string_agg(distinct plan_id_2026, ', ' order by plan_id_2026) as predecessor_plan_ids
    from rate_changes
    group by plan_id_2027
)

select
    c.plan_id_2027,
    p.state,
    p.issuer_id,
    p.issuer_name,
    p.plan_name,
    p.metal_level,
    p.metal_level_raw,
    p.plan_type,
    pred.predecessor_count,
    pred.predecessor_plan_ids,
    c.rating_area_count,
    c.avg_rate_2026,
    c.avg_rate_2027,
    c.avg_change_dollars,
    c.avg_change_pct
from plan_changes as c
-- Inner join adds the 2027 plan's details (insurer, metal level, plan type).
-- Every plan here came from the in-scope 2027 plans, so no rows drop.
join plans_2027 as p
    on p.plan_id = c.plan_id_2027
-- Inner join adds how many 2026 plans fed this 2027 plan, and which ones.
join predecessors as pred
    on pred.plan_id_2027 = c.plan_id_2027
