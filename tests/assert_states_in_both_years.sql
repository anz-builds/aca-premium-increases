-- Fails if any state in scope has plans in only one of the two years.
select state
from {{ ref('int_scope_plans') }}
group by state
having count(distinct plan_year) <> 2
