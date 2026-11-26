# Retention

Logs can't grow forever. `set_retention(topic, max_messages)` keeps only the newest
`max_messages` messages of the topic, now and after every publish. Offsets never change:
dropped messages are simply gone. A group positioned before the oldest retained message
continues from the oldest one (its `lag` counts only retained messages); `seek` below the oldest
retained offset raises `InvalidOffset`. `max_messages < 1` raises `InvalidArgument`.

*Interviewer's question:* who knows where the log starts now?
