insert into requests (from_id, to_id)
select :from_id, :to_id
where not exists (select 1 from connections
                  where user_low = least(:from_id::bigint, :to_id::bigint) and user_high = greatest(:from_id::bigint, :to_id::bigint))
union all
select :from_id, null   -- already connected: refuse (NOT NULL violation)
where exists (select 1 from connections
              where user_low = least(:from_id::bigint, :to_id::bigint) and user_high = greatest(:from_id::bigint, :to_id::bigint));
