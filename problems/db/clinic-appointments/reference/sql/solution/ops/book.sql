insert into appointments (doctor_id, patient_id, starts_at, minutes, ends_at)
values (:doctor_id, :patient_id, :starts_at, :minutes, :starts_at::timestamptz + :minutes * interval '1 minute')
returning id;
