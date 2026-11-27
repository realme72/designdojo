select coalesce(sum(p.monthly_price), 0)
from subscriptions s join plans p on p.id = s.plan_id
where tstzrange(s.start_at, s.end_at) @> :at::timestamptz;
