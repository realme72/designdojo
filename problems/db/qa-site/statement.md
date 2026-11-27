# Q&A Site (Stack Overflow)

> **Interview questions** (tab next to Problem): start there.

Design the database of a Q&A site (**PostgreSQL 17**).

## Requirements

1. **Users** (unique name). **Questions** have an author, a title, 1 to 5 **tags** (tag names are
   unique) and a creation time. **Answers** belong to a question.
2. Users **vote** (+1/−1) on questions and on answers: once per user per post, not on their own
   posts. Voting again changes the vote.
3. The asker may **accept** one answer, which must be an answer **to that question**.
4. **Reputation**: +5 per upvote on a user's question, +10 per upvote on their answer, −2 per
   downvote on either, +15 for each of their accepted answers.

## Operations

| Operation | Returns |
|---|---|
| `add_user(:name)` | one row: `id` |
| `ask(:user_id, :title, :tags, :asked_at)` | one row: `id` (`:tags` is a text array) |
| `answer(:question_id, :user_id, :body)` | one row: `id` |
| `vote_question(:user_id, :question_id, :value)`, `vote_answer(:user_id, :answer_id, :value)` | nothing |
| `accept(:question_id, :answer_id)` | nothing (replaces an earlier accepted answer) |
| `reputation(:user_id)` | a single value |
| `unanswered(:tag)` | rows `id`, `title`: questions with that tag and no answers, oldest first |
| `tag_leaders(:tag, :n)` | rows `name`, `score`: users by total score (sum of votes) of their answers to questions with that tag; ties by name |
