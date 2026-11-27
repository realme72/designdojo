insert into events (shipment_id, status, location, at)
select (select id from shipments where tracking_no = :tracking_no), :status, :location, :at;
