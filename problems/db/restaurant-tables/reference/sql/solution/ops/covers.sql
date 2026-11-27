select coalesce(sum(party_size), 0) from reservations
where not cancelled
  and starts_at >= (:day::date)::timestamp at time zone 'UTC'
  and starts_at <  (:day::date + 1)::timestamp at time zone 'UTC';
