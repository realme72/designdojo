select w.code as warehouse, m.change, m.reason from movements m join warehouses w on w.id = m.warehouse_id
where m.product_id = :product_id order by m.id;
