with old as (select id, status from issue_keys where issue_key = :issue_key),
upd as (update issues i set status = :status from old where i.id = old.id returning i.id, old.status as from_status)
insert into issue_history (issue_id, from_status, to_status, changed_at)
select id, from_status, :status, :at from upd where from_status <> :status;
