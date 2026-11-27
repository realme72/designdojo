# Chat Application (WhatsApp)

Design the messaging core of a chat app: direct messages, groups with admins, unread
counts and blocking.

## Requirements

1. Conversations are named `dm:<other user>` (from each participant's point of view) or
   `group:<group_id>`.
2. `send_direct(from_user, to_user, text)` → message id. Messaging yourself or empty text →
   `InvalidMessage`; if `to_user` has blocked `from_user` → `Blocked`.
3. `create_group(group_id, owner)` (repeated → `DuplicateGroup`); the owner is a member and
   admin. `add_member(group_id, by, user)` / `remove_member(group_id, by, user)` /
   `promote(group_id, by, user)` need `by` to be an admin → `Forbidden`. Removing the last
   admin is not allowed → `Forbidden`. Unknown group → `UnknownGroup`.
4. `send_group(group_id, from_user, text)` → message id; non-members → `NotMember`.
5. Members see only group messages sent **while they were members**.
   `messages(user, conversation)` lists `{id, from_user, text}` oldest first.
6. `unread(user)` → `{conversation, count}` for conversations with unread messages, sorted
   by conversation. Your own messages are never unread. `mark_read(user, conversation)`
   clears it.
7. `block(user, other)` / `unblock(user, other)`.
8. A busy group gets many messages at once: none lost, ids unique, everyone's unread exact.

## Things an interviewer will push on

- Fan-out on write (per-user inbox) vs on read (per-conversation log + read pointers)?
- How do delivery receipts (sent/delivered/read) fit in?
- How would you shard conversations across servers?
