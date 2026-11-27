create table courses (id bigint generated always as identity primary key, title text not null);
create table students (id bigint generated always as identity primary key, name text not null);

create table lessons (
  id        bigint generated always as identity primary key,
  course_id bigint not null references courses (id),
  title     text not null,
  position  int not null check (position >= 1),
  unique (course_id, position),
  unique (course_id, id)
);

create table enrollments (
  student_id bigint not null references students (id),
  course_id  bigint not null references courses (id),
  primary key (student_id, course_id)
);
create index enrollments_course_idx on enrollments (course_id);

create table completions (
  student_id   bigint not null,
  course_id    bigint not null,
  lesson_id    bigint not null,
  completed_at timestamptz not null,
  primary key (student_id, lesson_id),
  foreign key (student_id, course_id) references enrollments (student_id, course_id),
  foreign key (course_id, lesson_id) references lessons (course_id, id)
);
create index completions_course_idx on completions (course_id, lesson_id);
