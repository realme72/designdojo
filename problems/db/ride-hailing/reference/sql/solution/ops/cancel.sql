update trips set status = 'CANCELLED' where id = :trip_id and status = 'ACCEPTED';
