select d::date as day,
       coalesce((select sum(amount) from transactions t
                 where t.account_id = :account_id
                   and t.posted_at < (d::date + 1)::timestamp at time zone 'UTC'), 0) as balance
from generate_series(:from_day::date, :to_day::date, interval '1 day') d
order by d;
