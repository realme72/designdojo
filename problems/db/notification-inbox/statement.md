# Notification Inbox

> **Interview questions** (tab next to Problem): start there.

Design the storage behind an in-app notification inbox (**PostgreSQL 17**).

## Requirements

1. **Users** have a name. Notifications have a **type** from a fixed set: `LIKE`, `COMMENT`,
   `FOLLOW`, `SYSTEM`, a text, and a creation time.
2. Producers may retry: each notification carries an **idempotency key**; the same key for
   the same user creates it only once (the retry returns the original id).
3. Users can **mute** notification types; muted types are not stored at all.
4. Notifications are unread until read; users can mark one or **all** as read.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)` | one row: `id` |
| `notify(:user_id, :type, :text, :key, :created_at)` | rows `id`: the notification's id (also on a retry); no rows if the type is muted |
| `mute(:user_id, :type)`, `unmute(:user_id, :type)` | nothing |
| `mark_read(:notification_id)`, `mark_all_read(:user_id)` | nothing |
| `unread_count(:user_id)` | a single value |
| `inbox(:user_id, :n)` | rows `type`, `text`, `read`: newest first, ties by id descending |
