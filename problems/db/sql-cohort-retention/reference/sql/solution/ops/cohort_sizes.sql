select date_trunc('month', signed_up_at at time zone 'UTC')::date as cohort, count(*) as users
from users group by 1 order by 1;
