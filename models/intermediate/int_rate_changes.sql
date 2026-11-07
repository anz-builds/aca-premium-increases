-- One row per matched plan pair and rating area priced in both years.
-- Rule 2: compare the same plan in the same rating area (age 40, non-tobacco).

with pairs as (
    select * from {{ ref('int_plan_pairs') }}
),

rates as (
    select * from {{ ref('int_scope_rates') }}
)

select
    pairs.pair_key || '|' || r26.rating_area           as pair_area_key,
    pairs.pair_key,
    pairs.plan_id_2026,
    pairs.plan_id_2027,
    pairs.state,
    pairs.issuer_id,
    pairs.issuer_name,
    pairs.metal_level,
    pairs.plan_type,
    r26.rating_area,
    r26.rate_age_40                                     as rate_2026,
    r27.rate_age_40                                     as rate_2027,
    r27.rate_age_40 - r26.rate_age_40                   as change_dollars,
    -- Stored as a fraction: 0.05 means a 5% increase
    (r27.rate_age_40 - r26.rate_age_40) / r26.rate_age_40  as change_pct
from pairs
-- Inner join: the 2026 plan's price in each rating area it was sold in.
join rates as r26
    on r26.plan_key = pairs.plan_key_2026
-- Inner join: the 2027 plan's price in the same rating area. Areas priced
-- in only one of the two years drop out, so every row is like-for-like.
join rates as r27
    on r27.plan_key = pairs.plan_key_2027
   and r27.rating_area = r26.rating_area
