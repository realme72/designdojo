update rentals r
set status = 'RETURNED', km = :km,
    charge = (r.to_day - r.from_day) * v.daily_rate + greatest(0, :km - 200 * (r.to_day - r.from_day)) * 8.00
from vehicles v
where v.id = r.vehicle_id and r.id = :rental_id and r.status = 'BOOKED'
returning r.charge;
