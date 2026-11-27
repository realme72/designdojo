update rentals set status = 'CANCELLED' where id = :rental_id and status = 'BOOKED';
