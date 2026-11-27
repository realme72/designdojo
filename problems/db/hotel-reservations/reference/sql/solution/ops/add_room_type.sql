insert into room_types (name, nightly_rate) values (:name, :nightly_rate) returning id;
