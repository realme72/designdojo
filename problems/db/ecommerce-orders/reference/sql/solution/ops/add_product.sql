insert into products (sku, name, price, stock) values (:sku, :name, :price, :stock) returning id;
