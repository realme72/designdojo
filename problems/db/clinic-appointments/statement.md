# Clinic Appointments (Practo)

> **Interview questions** (tab next to Problem): start there.

Design appointment booking for a clinic (**PostgreSQL 17**).

## Requirements

1. **Doctors** have a name and a specialty; **patients** a name.
2. An **appointment** is a doctor, a patient, a start time and a length of 15, 30, 45 or 60
   minutes. Its status is `BOOKED` or `CANCELLED`.
3. A doctor never has two booked appointments that overlap, and neither does a **patient**.
   Back-to-back is fine; cancelled appointments block nothing.

## Operations

| Operation | Returns |
|---|---|
| `add_doctor(:name, :specialty)`, `add_patient(:name)` | one row: `id` |
| `book(:doctor_id, :patient_id, :starts_at, :minutes)` | one row: `id` |
| `cancel(:appointment_id)` | nothing |
| `doctor_day(:doctor_id, :day)` | rows `starts_at`, `patient`: booked appointments that UTC day, by time |
| `free_slots(:doctor_id, :day)` | rows `slot`: 30-minute slots from 09:00 to 17:00 UTC (last slot 16:30) not overlapping a booked appointment, by time |
| `busiest_specialties(:from, :to)` | rows `specialty`, `appointments`: booked appointments starting in `[from, to)`, by count desc then specialty |
