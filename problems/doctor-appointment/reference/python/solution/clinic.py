from __future__ import annotations

import itertools
import threading
from collections import defaultdict
from dataclasses import dataclass, field

from contract import (Appointment, Clinic, Clock, DuplicateDoctor, InvalidState, InvalidWindow, OpenSlot,
                      PatientConflict, SlotUnavailable, UnknownAppointment, UnknownDoctor)


@dataclass
class Doctor:
    id: str
    specialty: str
    slot_seconds: int
    windows: list[tuple[int, int]] = field(default_factory=list)
    slots: dict[int, str | None] = field(default_factory=dict)  # slot start -> appointment id (None = free)


def split(start: int, end: int, size: int) -> list[int]:
    return list(range(start, end - size + 1, size))


class ClinicService(Clinic):
    def __init__(self, clock: Clock):
        self._clock = clock
        self._doctors: dict[str, Doctor] = {}
        self._by_specialty: defaultdict[str, list[Doctor]] = defaultdict(list)
        self._appts: dict[str, tuple[str, Appointment]] = {}  # id -> (patient, appointment)
        self._by_patient: defaultdict[str, dict[str, Appointment]] = defaultdict(dict)
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def _doctor(self, did: str) -> Doctor:
        d = self._doctors.get(did)
        if d is None:
            raise UnknownDoctor(did)
        return d

    def add_doctor(self, doctor_id: str, specialty: str, slot_minutes: int) -> None:
        with self._lock:
            if doctor_id in self._doctors:
                raise DuplicateDoctor(doctor_id)
            d = Doctor(doctor_id, specialty, slot_minutes * 60)
            self._doctors[doctor_id] = d
            self._by_specialty[specialty].append(d)

    def add_availability(self, doctor_id: str, start: int, end: int) -> None:
        with self._lock:
            d = self._doctor(doctor_id)
            if end <= start or any(start < e and s < end for s, e in d.windows):
                raise InvalidWindow(f"{start}..{end}")
            d.windows.append((start, end))
            for s in split(start, end, d.slot_seconds):
                d.slots[s] = None

    def available_slots(self, specialty: str, start: int, end: int) -> list[OpenSlot]:
        with self._lock:
            now = self._clock.now()
            found = [OpenSlot(d.id, s) for d in self._by_specialty.get(specialty, [])
                     for s, taken in d.slots.items() if taken is None and start <= s < end and s >= now]
            return sorted(found, key=lambda o: (o.start, o.doctor_id))

    def book(self, patient: str, doctor_id: str, start: int) -> str:
        with self._lock:
            d = self._doctor(doctor_id)
            if d.slots.get(start, "missing") is not None or start < self._clock.now():
                raise SlotUnavailable(f"{doctor_id}@{start}")
            end = start + d.slot_seconds
            if any(a.start < end and start < a.end for a in self._by_patient[patient].values()):
                raise PatientConflict(patient)
            appt = Appointment(f"A{next(self._ids)}", doctor_id, start, end)
            d.slots[start] = appt.id
            self._appts[appt.id] = (patient, appt)
            self._by_patient[patient][appt.id] = appt
            return appt.id

    def cancel(self, appointment_id: str) -> None:
        with self._lock:
            found = self._appts.get(appointment_id)
            if found is None:
                raise UnknownAppointment(appointment_id)
            patient, appt = found
            if self._clock.now() >= appt.start:
                raise InvalidState("appointment already started")
            del self._appts[appointment_id]
            del self._by_patient[patient][appointment_id]
            self._doctors[appt.doctor_id].slots[appt.start] = None

    def reschedule(self, appointment_id: str, new_start: int) -> None:
        with self._lock:
            found = self._appts.get(appointment_id)
            if found is None:
                raise UnknownAppointment(appointment_id)
            patient, old = found
            now = self._clock.now()
            if now >= old.start:
                raise InvalidState("appointment already started")
            d = self._doctors[old.doctor_id]
            if d.slots.get(new_start, "missing") is not None or new_start < now:
                raise SlotUnavailable(f"{d.id}@{new_start}")
            end = new_start + d.slot_seconds
            if any(a.id != old.id and a.start < end and new_start < a.end for a in self._by_patient[patient].values()):
                raise PatientConflict(patient)
            moved = Appointment(old.id, d.id, new_start, end)
            d.slots[old.start], d.slots[new_start] = None, moved.id
            self._appts[moved.id] = (patient, moved)
            self._by_patient[patient][moved.id] = moved

    def appointments(self, patient: str) -> list[Appointment]:
        with self._lock:
            return sorted(self._by_patient[patient].values(), key=lambda a: a.start)
