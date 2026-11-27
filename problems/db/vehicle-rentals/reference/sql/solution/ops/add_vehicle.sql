insert into vehicles (plate, category, daily_rate) values (:plate, :category, :daily_rate) returning id;
