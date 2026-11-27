select d::date as day, count(distinct l.user_id) as users
from generate_series(:from_day::date, :to_day::date, interval '1 day') d
left join logins l on (l.logged_at at time zone 'UTC')::date = d::date
group by d order by d;
