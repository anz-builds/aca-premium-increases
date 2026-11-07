-- One row per plan, rating area, rate start date and year: the age-40, non-tobacco price.
-- IndividualRate is the non-tobacco rate (CMS Rate PUF data dictionary).
-- The start date is part of the key because small-group (SHOP) plans can have
-- a new rate each quarter; in-scope individual plans have one (profile check 9).

with rates as (
    select * from {{ source('cms', 'rate_2026') }}
    union all by name
    select * from {{ source('cms', 'rate_2027') }}
)

select
    BusinessYear || '-' || PlanId || '-' || RatingAreaId
        || '-' || RateEffectiveDate                         as rate_key,
    BusinessYear || '-' || PlanId                           as plan_key,
    cast(BusinessYear as integer)                           as plan_year,
    PlanId                                                  as plan_id,
    StateCode                                               as state,
    RatingAreaId                                            as rating_area,
    cast(RateEffectiveDate as date)                         as rate_effective_date,
    try_cast(IndividualRate as double)                      as rate_age_40
from rates
where Age = '40'