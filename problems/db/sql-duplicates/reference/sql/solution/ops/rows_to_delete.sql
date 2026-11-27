select id from (
  select id, row_number() over (partition by lower(trim(email)) order by created_at, id) as rn from signups
) x where rn > 1 order by id;
