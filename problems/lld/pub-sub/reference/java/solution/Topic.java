package solution;

import contract.Message;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;

/** Append-only log; appends and reads are serialised on the topic. */
final class Topic {
    private final List<String> log = new ArrayList<>();
    private long base = 0;      // offset of log.get(0); older messages were dropped by retention
    private int retention = 0;  // 0 = keep everything
    final ConcurrentHashMap<String, Subscription> subscriptions = new ConcurrentHashMap<>();

    private void trim() {
        if (retention > 0 && log.size() > retention) {
            int drop = log.size() - retention;
            log.subList(0, drop).clear();
            base += drop;
        }
    }

    synchronized void setRetention(int maxMessages) {
        retention = maxMessages;
        trim();
    }

    synchronized long append(String payload) {
        log.add(payload);
        trim();
        return base + log.size() - 1;
    }

    synchronized long start() {
        return base;
    }

    synchronized long end() {
        return base + log.size();
    }

    synchronized List<Message> read(long start, int count) {
        List<Message> out = new ArrayList<>();
        long from = Math.max(start, base);
        long stop = Math.min(from + count, base + log.size());
        for (long i = from; i < stop; i++) out.add(new Message(i, log.get((int) (i - base))));
        return out;
    }
}
