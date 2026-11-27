select d.specialty, count(*) as appointments
from appointments a join doctors d on d.id = a.doctor_id
where a.status = 'BOOKED' and a.starts_at >= :from and a.starts_at < :to
group by d.specialty
order by appointments desc, d.specialty;
