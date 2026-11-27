select txn_id, amount, sum(amount) over (order by txn_id, id) as balance_after
from entries where account_id = :account_id
order by txn_id, id;
