package solution;

import contract.Algorithm;

import java.util.ArrayDeque;

final class Limiters {
    private Limiters() {}

    static Limiter create(Algorithm algorithm, int limit, long window, long now) {
        return switch (algorithm) {
            case FIXED_WINDOW -> new FixedWindow(limit, window);
            case SLIDING_WINDOW_LOG -> new SlidingLog(limit, window);
            case TOKEN_BUCKET -> new TokenBucket(limit, window, now);
            case SLIDING_WINDOW_COUNTER -> new SlidingCounter(limit, window);
        };
    }

    static final class FixedWindow implements Limiter {
        private final int limit;
        private final long window;
        private long current = Long.MIN_VALUE;
        private int count;

        FixedWindow(int limit, long window) { this.limit = limit; this.window = window; }

        public boolean allow(long now) {
            long w = Math.floorDiv(now, window);
            if (w != current) { current = w; count = 0; }
            if (count < limit) { count++; return true; }
            return false;
        }
    }

    static final class SlidingLog implements Limiter {
        private final int limit;
        private final long window;
        private final ArrayDeque<Long> log = new ArrayDeque<>();

        SlidingLog(int limit, long window) { this.limit = limit; this.window = window; }

        public boolean allow(long now) {
            while (!log.isEmpty() && log.peekFirst() <= now - window) log.pollFirst();
            if (log.size() < limit) { log.addLast(now); return true; }
            return false;
        }
    }

    /** Two aligned fixed-window counters; the previous one weighted by its remaining overlap. */
    static final class SlidingCounter implements Limiter {
        private final long limit;
        private final long window;
        private long current = Long.MIN_VALUE;
        private long curr;
        private long prev;

        SlidingCounter(int limit, long window) { this.limit = limit; this.window = window; }

        public boolean allow(long now) {
            long w = Math.floorDiv(now, window);
            if (w != current) {
                prev = (current != Long.MIN_VALUE && w == current + 1) ? curr : 0;
                current = w;
                curr = 0;
            }
            long elapsed = now - w * window;
            if (prev * (window - elapsed) + curr * window < limit * window) { curr++; return true; }
            return false;
        }
    }

    /** Tokens scaled by window so refills are exact. */
    static final class TokenBucket implements Limiter {
        private final long limit;
        private final long window;
        private long scaled;
        private long last;

        TokenBucket(int limit, long window, long now) {
            this.limit = limit; this.window = window; this.scaled = limit * window; this.last = now;
        }

        public boolean allow(long now) {
            scaled = Math.min(limit * window, scaled + (now - last) * limit);
            last = now;
            if (scaled >= window) { scaled -= window; return true; }
            return false;
        }
    }
}
