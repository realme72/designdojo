select a.starts_at, p.name as patient
from appointments a join patients p on p.id = a.patient_id
where a.doctor_id = :doctor_id and a.status = 'BOOKED'
  and a.starts_at >= (:day::date)::timestamp at time zone 'UTC'
  and a.starts_at <  (:day::date + 1)::timestamp at time zone 'UTC'
order by a.starts_at;
