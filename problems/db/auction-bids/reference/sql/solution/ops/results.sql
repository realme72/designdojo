select i.title, u.name as winner, i.current_price as price
from items i join users u on u.id = i.current_leader
where i.ends_at <= :at
order by i.title;
