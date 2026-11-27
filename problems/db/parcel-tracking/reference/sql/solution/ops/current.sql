select e.status, e.location from events e join shipments s on s.id = e.shipment_id
where s.tracking_no = :tracking_no order by e.at desc, e.id desc limit 1;
