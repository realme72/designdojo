update sessions x
set exited_at = :at,
    fee = greatest(1, ceil(extract(epoch from (:at::timestamptz - x.entered_at)) / 3600)) * t.hourly_rate
from spots s join spot_types t on t.type = s.type
where s.id = x.spot_id
  and x.exited_at is null and x.vehicle_id = (select id from vehicles where plate = :plate)
returning x.fee;
