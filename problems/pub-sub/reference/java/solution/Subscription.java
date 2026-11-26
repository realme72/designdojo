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
        position += batch.size();
        return batch;
    }

    synchronized long lag() {
        return topic.end() - position;
    }

    synchronized void seek(long offset) {
        if (offset < 0 || offset > topic.end()) throw new InvalidOffset("offset " + offset);
        position = offset;
    }
}
