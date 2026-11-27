select u.name,
       coalesce((select sum(amount) from expenses e where e.group_id = m.group_id and e.paid_by = m.user_id), 0)
     - coalesce((select sum(amount) from shares s where s.group_id = m.group_id and s.user_id = m.user_id), 0)
     + coalesce((select sum(amount) from settlements x where x.group_id = m.group_id and x.from_id = m.user_id), 0)
     - coalesce((select sum(amount) from settlements x where x.group_id = m.group_id and x.to_id = m.user_id), 0)
       as balance
from members m join users u on u.id = m.user_id
where m.group_id = :group_id
order by u.name;
