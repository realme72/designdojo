with u as (
  update attendees set response = :response
  where event_id = :event_id and user_id = :user_id and :response <> 'INVITED'
  returning 1
)
insert into attendees (event_id, user_id) select null, null where not exists (select 1 from u);   -- not invited: refuse
