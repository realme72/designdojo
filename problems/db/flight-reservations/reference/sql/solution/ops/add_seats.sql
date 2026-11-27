insert into seats (flight_id, seat_no, class)
select :flight_id, n, :class from generate_series(:first_no, :last_no) n;
