# Doctor Appointment Booking (Practo)

Design appointment booking for a clinic network. Times are epoch seconds.

## Requirements

1. `add_doctor(doctor_id, specialty, slot_minutes)`; repeated id → `DuplicateDoctor`.
2. `add_availability(doctor_id, start, end)`: a working window split into consecutive
   slots of `slot_minutes` starting at `start` (a trailing piece shorter than a slot is
   dropped). `end ≤ start` → `InvalidWindow`; overlapping an existing window of that
   doctor → `InvalidWindow`. Unknown doctor → `UnknownDoctor`.
3. `available_slots(specialty, start, end)` → free slots `{doctor_id, start}` of that
   specialty whose start is within `[start, end)` and not in the past (`≥ now`), sorted by
   time then doctor id.
4. `book(patient, doctor_id, start)` → appointment id. Not a free future slot of that doctor
   → `SlotUnavailable`; the patient already has an appointment overlapping this slot (any
   doctor) → `PatientConflict`; unknown doctor → `UnknownDoctor`.
5. `cancel(appointment_id)` frees the slot; only before the appointment starts → else
   `InvalidState`. Unknown or already cancelled → `UnknownAppointment`.
6. `appointments(patient)` → `{id, doctor_id, start, end}` sorted by start.
7. Patients book concurrently: a slot is never booked twice.

## Things an interviewer will push on

- How do you model slots: precomputed objects or computed on demand?
- How would you add consultation types with different lengths?
- Search across thousands of doctors: what index helps?
