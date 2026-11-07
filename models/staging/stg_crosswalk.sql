-- One row per 2026 medical plan, 2027 plan and crosswalk reason.
-- The raw file has one row per county (and sometimes ZIP code); this collapses those.

select distinct
    PlanID_2026                         as plan_id_2026,
    PlanID_2027                         as plan_id_2027,
    State                               as state,
    cast(ReasonForCrosswalk as integer) as crosswalk_reason
from {{ source('cms', 'crosswalk_2027') }}
where DentalPlan = 'N'