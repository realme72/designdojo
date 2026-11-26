# Delete for everyone

Users can delete their own messages: `delete_message(user, message_id)`. A deleted message
disappears from `messages()` for everyone and no longer counts as unread. Only the sender may
delete (`Forbidden`); an unknown or already-deleted id raises `UnknownMessage`. Works for direct
and group messages.

*Interviewer's question:* where does a message id lead you: which conversation owns it?
