with running as (
  select t.account_id, t.posted_at, t.id,
         sum(t.amount) over (partition by t.account_id order by t.posted_at, t.id rows between unbounded preceding and current row) as bal
  from transactions t
)
select distinct on (a.owner) a.owner, r.posted_at
from running r join accounts a on a.id = r.account_id
where r.bal < 0
order by a.owner, r.posted_at, r.id;
