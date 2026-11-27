with doomed as (
  select id from (
    select id, row_number() over (partition by lower(trim(email)) order by created_at, id) as rn from signups
  ) x where rn > 1
),
d as (delete from signups s using doomed where s.id = doomed.id returning s.id)
select id from d order by id;
