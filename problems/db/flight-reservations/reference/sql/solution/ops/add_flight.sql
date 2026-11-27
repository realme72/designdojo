insert into flights (code, origin, destination, departs_at, arrives_at) values (:code, :origin, :destination, :departs_at, :arrives_at) returning id;
