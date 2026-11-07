-- Fails if any in-scope age-40 price is zero or negative.
select *
from {{ ref('int_scope_rates') }}
where rate_age_40 <= 0
