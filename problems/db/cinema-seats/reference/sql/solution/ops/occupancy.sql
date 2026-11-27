select sh.starts_at,
       (select count(*) from booked_seats b where b.show_id = sh.id) as booked,
       (select count(*) from seats st where st.screen_id = sh.screen_id) as capacity
from shows sh where sh.movie = :movie order by sh.starts_at;
