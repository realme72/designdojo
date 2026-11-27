create extension if not exists btree_gist;

create table doctors (id bigint generated always as identity primary key, name text not null, specialty text not null);
create table patients (id bigint generated always as identity primary key, name text not null);

create table appointments (
  id         bigint generated always as identity primary key,
  doctor_id  bigint not null references doctors (id),
  patient_id bigint not null references patients (id),
  starts_at  timestamptz not null,
  minutes    int not null check (minutes in (15, 30, 45, 60)),
  ends_at    timestamptz not null,   -- timestamptz + interval isn't immutable, so it can't be a generated column
  status     text not null default 'BOOKED' check (status in ('BOOKED', 'CANCELLED')),
  check (ends_at = starts_at + minutes * interval '1 minute'),
  exclude using gist (doctor_id with =, tstzrange(starts_at, ends_at) with &&) where (status = 'BOOKED'),
  exclude using gist (patient_id with =, tstzrange(starts_at, ends_at) with &&) where (status = 'BOOKED')
);
create index appointments_start_idx on appointments (starts_at);
