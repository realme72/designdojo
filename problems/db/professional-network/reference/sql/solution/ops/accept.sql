with acc as (
  update requests set status = 'ACCEPTED'
  where from_id = :from_id and to_id = :to_id and status = 'PENDING'
  returning from_id, to_id
)
insert into connections (user_low, user_high)
select least(from_id, to_id), greatest(from_id, to_id) from acc
union all
select null, null where not exists (select 1 from acc);   -- nothing pending: refuse
