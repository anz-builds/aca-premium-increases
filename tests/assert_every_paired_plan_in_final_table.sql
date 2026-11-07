-- Business rule: every 2027 plan in a matched pair (int_plan_pairs)
-- appears in the final table. Returns any that are missing.
select distinct pairs.plan_id_2027
from {{ ref('int_plan_pairs') }} as pairs
-- Left join keeps every paired plan, so missing ones show up as nulls.
left join {{ ref('plan_premium_changes') }} as final
    on final.plan_id_2027 = pairs.plan_id_2027
where final.plan_id_2027 is null
