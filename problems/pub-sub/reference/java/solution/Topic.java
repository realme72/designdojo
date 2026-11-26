package solution;

import contract.Message;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;

/** Append-only log; appends and reads are serialised on the topic. */
final class Topic {
    private final List<String> log = new ArrayList<>();
    final ConcurrentHashMap<String, Subscription> subscriptions = new ConcurrentHashMap<>();

    synchronized long append(String payload) {
        log.add(payload);
        return log.size() - 1;
    }

    synchronized long end() {
        return log.size();
    }

    synchronized List<Message> read(long start, int count) {
        List<Message> out = new ArrayList<>();
        for (long i = start; i < Math.min(start + count, log.size()); i++) out.add(new Message(i, log.get((int) i)));
        return out;
    }
}
