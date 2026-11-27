select posted_at, amount,
       sum(amount) over (order by posted_at, id rows between unbounded preceding and current row) as balance
from transactions where account_id = :account_id order by posted_at, id;
