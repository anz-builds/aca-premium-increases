-- Rule 2 business-rule test. Fails if any price change doesn't trace back to
-- the 2026 plan's price and the 2027 plan's price in the SAME rating area.

select changes.pair_area_key
from {{ ref('int_rate_changes') }} as changes
join {{ ref('int_plan_pairs') }} as pairs
    on pairs.pair_key = changes.pair_key
left join {{ ref('int_scope_rates') }} as r26
    on r26.plan_key = pairs.plan_key_2026
   and r26.rating_area = changes.rating_area
   and r26.rate_age_40 = changes.rate_2026
left join {{ ref('int_scope_rates') }} as r27
    on r27.plan_key = pairs.plan_key_2027
   and r27.rating_area = changes.rating_area
   and r27.rate_age_40 = changes.rate_2027
where r26.plan_key is null
   or r27.plan_key is null
