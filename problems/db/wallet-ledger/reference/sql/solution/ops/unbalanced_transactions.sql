select t.id as txn_id
from transactions t left join entries e on e.txn_id = t.id
group by t.id having coalesce(sum(e.amount), 0) <> 0
order by t.id;
