# Reschedule

Patients can move an appointment: `reschedule(appointment_id, new_start)` to another open slot
of the **same** doctor. The appointment keeps its id. It's all-or-nothing: if the new slot is
unavailable (`SlotUnavailable`) or clashes with the patient's *other* appointments
(`PatientConflict`), the original booking is untouched. Unknown id → `UnknownAppointment`;
an appointment that has already started → `InvalidState`.

*Interviewer's question:* can you reuse book + cancel, and what breaks if you do?
