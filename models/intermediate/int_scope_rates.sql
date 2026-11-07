-- Age-40 prices for in-scope plans only.
-- One row per plan, rating area and year (profile check 9 showed in-scope
-- plans have one price per rating area; the unique test on plan_area_key enforces it).

select
    rates.plan_key || '-' || rates.rating_area  as plan_area_key,
    rates.*
from {{ ref('stg_rates') }} as rates
-- Inner join keeps only prices for in-scope plans; it drops dental,
-- small-group, platinum and catastrophic plans, and Oregon.
join {{ ref('int_scope_plans') }} as plans
    on rates.plan_key = plans.plan_key
