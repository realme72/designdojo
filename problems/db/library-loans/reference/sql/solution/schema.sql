create table books (id bigint generated always as identity primary key, isbn text not null unique, title text not null);
create table copies (
  id      bigint generated always as identity primary key,
  book_id bigint not null references books (id),
  barcode text not null unique
);
create index copies_book_idx on copies (book_id);
create table members (id bigint generated always as identity primary key, name text not null);

create table loans (
  id          bigint generated always as identity primary key,
  copy_id     bigint not null references copies (id),
  member_id   bigint not null references members (id),
  loaned_at   timestamptz not null,
  due_at      timestamptz not null,
  returned_at timestamptz,
  check (due_at > loaned_at),
  check (returned_at is null or returned_at >= loaned_at)
);
create unique index loans_one_active_per_copy on loans (copy_id) where returned_at is null;
create index loans_member_active_idx on loans (member_id) where returned_at is null;

create function loan_limit() returns trigger language plpgsql as $$
begin
  perform 1 from members where id = new.member_id for update;   -- serialize this member's checkouts
  if (select count(*) from loans where member_id = new.member_id and returned_at is null) >= 3 then
    raise exception 'member % already has 3 active loans', new.member_id;
  end if;
  return new;
end $$;
create trigger loans_limit before insert on loans for each row execute function loan_limit();
