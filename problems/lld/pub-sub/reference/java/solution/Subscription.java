package solution;

import contract.InvalidOffset;
import contract.Message;

import java.util.List;

/** One consumer group's position in one topic; read-and-advance is atomic. */
final class Subscription {
    private final Topic topic;
    private long position;

    Subscription(Topic topic, long position) {
        this.topic = topic;
        this.position = position;
    }

    synchronized List<Message> poll(int max) {
        List<Message> batch = topic.read(position, max);
        if (!batch.isEmpty()) position = batch.get(batch.size() - 1).offset() + 1;
        return batch;
    }

    synchronized long lag() {
        return topic.end() - Math.max(position, topic.start());
    }

    synchronized void seek(long offset) {
        if (offset < topic.start() || offset > topic.end()) throw new InvalidOffset("offset " + offset);
        position = offset;
    }
}
