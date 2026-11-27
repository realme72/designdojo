with s as (insert into screens (name) values (:name) returning id),
g as (
  insert into seats (screen_id, row_label, number)
  select s.id, chr(64 + r), n from s, generate_series(1, :rows) r, generate_series(1, :seats_per_row) n
)
select id from s;
