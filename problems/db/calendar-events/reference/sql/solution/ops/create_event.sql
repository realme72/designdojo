with e as (
  insert into events (organizer_id, title, starts_at, ends_at)
  values (:organizer_id, :title, :starts_at, :ends_at) returning id, organizer_id
),
a as (insert into attendees (event_id, user_id, response) select id, organizer_id, 'ACCEPTED' from e)
select id from e;
