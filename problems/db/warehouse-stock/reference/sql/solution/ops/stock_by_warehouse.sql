select w.code as warehouse, s.qty from stock s join warehouses w on w.id = s.warehouse_id
where s.product_id = :product_id order by w.code;
