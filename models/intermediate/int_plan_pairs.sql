-- One row per matched plan pair: a 2026 plan and the 2027 plan that continues it.
-- Rule 3 (same plan only): crosswalk reason 0 (same plan ID) or 1 (same plan, new ID).
-- Both plans must be in scope in their own year.

with same_plan_matches as (
    select distinct plan_id_2026, plan_id_2027, crosswalk_reason
    from {{ ref('stg_crosswalk') }}
    where crosswalk_reason in (0, 1)
),

plans_2026 as (
    select * from {{ ref('int_scope_plans') }} where plan_year = 2026
),

plans_2027 as (
    select * from {{ ref('int_scope_plans') }} where plan_year = 2027
)

select
    m.plan_id_2026 || '>' || m.plan_id_2027     as pair_key,
    m.plan_id_2026,
    m.plan_id_2027,
    m.crosswalk_reason,
    p26.plan_key                                as plan_key_2026,
    p27.plan_key                                as plan_key_2027,
    p27.state,
    p27.issuer_id,
    p27.issuer_name,
    p27.metal_level,
    p27.plan_type,
    p26.issuer_id                               as issuer_id_2026,
    p26.metal_level                             as metal_level_2026,
    p26.plan_type                               as plan_type_2026
from same_plan_matches as m
-- Inner join keeps only matches whose 2026 plan is in scope.
join plans_2026 as p26
    on p26.plan_id = m.plan_id_2026
-- Inner join keeps only matches whose 2027 plan is also in scope
-- (drops plans that became platinum, catastrophic or small-group).
join plans_2027 as p27
    on p27.plan_id = m.plan_id_2027
