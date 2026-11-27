insert into spots (lot_id, number, type)
select :lot_id, base.n + g, :type
from (select coalesce(max(number), 0) as n from spots where lot_id = :lot_id) base, generate_series(1, :count) g;
