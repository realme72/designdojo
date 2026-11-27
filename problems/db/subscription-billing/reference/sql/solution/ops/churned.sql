select distinct c.email
from subscriptions s join customers c on c.id = s.customer_id
where s.end_at >= :from and s.end_at < :to
  and not exists (select 1 from subscriptions a where a.customer_id = s.customer_id
                  and tstzrange(a.start_at, a.end_at) @> :to::timestamptz)
order by c.email;
