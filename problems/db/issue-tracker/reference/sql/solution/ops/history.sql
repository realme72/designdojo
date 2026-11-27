select h.from_status, h.to_status from issue_history h join issue_keys k on k.id = h.issue_id
where k.issue_key = :issue_key order by h.id;
