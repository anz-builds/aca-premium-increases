-- One row per plan per year.
-- Plan Attributes has one row per plan variant. The profile showed every variant
-- of a plan shares the same state, insurer, metal level, plan type and market,
-- so they're part of the grouping: if they ever disagreed, the plan would get two
-- rows and the unique test on plan_key would fail.

with plan_variants as (
    select * from {{ source('cms', 'plan_attributes_2026') }}
    union all by name
    select * from {{ source('cms', 'plan_attributes_2027') }}
)

select
    BusinessYear || '-' || StandardComponentId          as plan_key,
    cast(BusinessYear as integer)                       as plan_year,
    StandardComponentId                                 as plan_id,
    StateCode                                           as state,
    IssuerId                                            as issuer_id,
    any_value(IssuerMarketplaceMarketingName)           as issuer_name,
    any_value(PlanMarketingName)                        as plan_name,
    MetalLevel                                          as metal_level_raw,
    -- Expanded Bronze is a bronze-level plan with slightly richer coverage
    case when MetalLevel = 'Expanded Bronze' then 'Bronze'
         else MetalLevel end                            as metal_level,
    PlanType                                            as plan_type,
    MarketCoverage                                      as market,
    DentalOnlyPlan = 'Yes'                              as is_dental_only
from plan_variants
group by all