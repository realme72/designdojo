# Q&A Site (Stack Overflow)

Design the core of a Q&A site: questions, answers, voting, reputation and moderation.

## Requirements

1. Every user starts with reputation 1. Post ids are unique across questions and answers.
2. `ask(user, question_id, title, tags)`: empty title, no tags, or more than 5 tags →
   `InvalidQuestion`. Repeated post id → `DuplicatePost`.
3. `answer(user, question_id, answer_id)`: unknown question → `UnknownPost`; a closed
   question → `QuestionClosed`; repeated id → `DuplicatePost`.
4. `vote(user, post_id, up)` on a question or answer. Voting on your own post → `SelfVote`.
   One vote per user per post: voting the same way again changes nothing; voting the other
   way switches the vote. Reputation for the post's author: upvote on a question +5, on an
   answer +10; any downvote −2. Switching a vote reverses the old effect first.
   `score(post_id)` = upvotes − downvotes.
5. `accept(user, answer_id)`: only the question's author (`Forbidden`). The answerer gets
   +15 (none when accepting your own answer). Accepting a different answer moves the +15:
   the previous answerer loses it. Unknown → `UnknownPost`.
6. `close(user, question_id)` needs reputation ≥ `close_threshold` (config) → else `Forbidden`.
7. `reputation(user)`; `search(tag)` → question ids with that tag, highest score first, ties by id.
8. Votes pour in concurrently on popular posts: nothing may be lost.

## Things an interviewer will push on

- Reputation rules change often: where do they live?
- Question vs Answer: shared base class (Post) or composition?
- How would badges or notifications hook into votes and accepts?
