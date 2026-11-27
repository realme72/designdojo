select coalesce(sum(total), 0) from orders where restaurant_id = :restaurant_id and status = 'DELIVERED';
