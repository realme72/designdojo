select s.type, count(x.id) as occupied, count(s.id) as total
from spots s left join sessions x on x.spot_id = s.id and x.exited_at is null
where s.lot_id = :lot_id group by s.type order by s.type;
