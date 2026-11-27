# Chat Messaging (WhatsApp)

> **Interview questions** (tab next to Problem): start there.

Design the database for a chat app with direct and group conversations (**PostgreSQL 17**).

## Requirements

1. **Users** have a name.
2. A **direct conversation** is between exactly two different users, and there is at most
   **one** per pair (whichever of the two starts it).
3. A **group** has a name and members; its creator is a member. Adding a member twice is rejected.
4. **Messages** belong to a conversation; only **members** of that conversation can send.
   Messages can't be empty.
5. Each member has a **read position** (the last message they have read). It never moves
   backwards.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)` | one row: `id` |
| `start_direct(:user_a, :user_b)` | one row: `conversation_id` (the existing one if the pair already has one) |
| `create_group(:name, :owner_id)` | one row: `conversation_id` |
| `add_member(:conversation_id, :user_id)` | nothing |
| `send(:conversation_id, :sender_id, :body, :sent_at)` | one row: `id` |
| `mark_read(:conversation_id, :user_id, :message_id)` | nothing |
| `inbox(:user_id)` | rows `conversation_id`, `title`, `last_message`, `unread`: the user's conversations that have messages, latest message first. Title: the group name, or the other person's name. Unread: messages after the read position, not sent by the user |
| `history(:conversation_id, :before_id, :n)` | rows `id`, `sender`, `body`: up to `n` messages older than `:before_id` (newest if NULL), newest first |
