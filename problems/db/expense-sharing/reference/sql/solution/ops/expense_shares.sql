select u.name, s.amount as share from shares s join users u on u.id = s.user_id
where s.expense_id = :expense_id order by u.name;
