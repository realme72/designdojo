insert into shows (screen_id, movie, starts_at, ends_at) values (:screen_id, :movie, :starts_at, :ends_at) returning id;
