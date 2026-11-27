# File Storage & Sharing (Google Drive)

> **Interview questions** (tab next to Problem): start there.

Design folders, files and sharing for a cloud drive (**PostgreSQL 17**).

## Requirements

1. **Users** own **folders**. A folder has a name and a parent folder (NULL = top level of the
   owner's drive). Names are unique among siblings: within a parent folder, or among an owner's
   top-level folders.
2. **Files** live in a folder, have a name (unique within the folder) and a size in bytes (≥ 0).
3. Folders can be **moved**, but never into themselves or their own subfolders.
4. A folder can be **shared** with a user as `VIEW` or `EDIT` (once per user and folder). Access
   is **inherited**: a share on a folder covers everything inside it, at any depth. Owners can
   always access their own items.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)` | one row: `id` |
| `create_folder(:owner_id, :parent_id, :name)` | one row: `id` |
| `upload(:folder_id, :name, :size_bytes)` | one row: `id` |
| `move_folder(:folder_id, :new_parent_id)` | nothing |
| `share(:folder_id, :user_id, :role)` | nothing |
| `can_view(:user_id, :file_id)` | a single value: true/false |
| `folder_size(:folder_id)` | a single value: bytes of all files inside, at any depth |
| `path(:file_id)` | a single value like `/Work/2030/report.pdf` |
