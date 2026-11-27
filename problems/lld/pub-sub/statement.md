# Pub-Sub Message Broker

Design an in-memory message broker in the style of Kafka: topics are append-only logs,
and consumer groups read them independently at their own pace.

## Requirements

1. `create_topic(name)`; repeated name → `DuplicateTopic`.
2. `publish(topic, payload)` appends a message and returns its offset (0, 1, 2, … per topic).
3. `subscribe(topic, group, from_beginning)` registers a consumer group on a topic. It
   starts at offset 0 if `from_beginning`, otherwise at the current end (only new
   messages). Subscribing the same group to the same topic twice → `DuplicateSubscription`.
4. `poll(topic, group, max)` returns up to `max` messages (`{offset, payload}`) from the
   group's position and advances it past them (auto-commit). Nothing new → empty list.
   `max < 1` → `InvalidArgument`.
5. Groups are independent: each group sees every message once; two groups both see all.
6. `lag(topic, group)` = messages published but not yet polled by the group.
7. `seek(topic, group, offset)` moves the group's position; valid range is `0..end`
   (inclusive, where end = number of messages) → otherwise `InvalidOffset`.
8. Unknown topic → `UnknownTopic`; group not subscribed to that topic → `UnknownGroup`.
9. Producers and consumers run concurrently: offsets are unique and gap-free, and within a
   group no message is delivered twice even when several consumers poll at once.

## Things an interviewer will push on

- Push (observer callbacks) vs pull (poll): trade-offs?
- How would you add partitions with ordering per key?
- What lock protects what? Can publishers and consumers avoid contending?
