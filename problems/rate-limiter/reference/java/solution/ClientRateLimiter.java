package solution;

import contract.Algorithm;
import contract.Clock;
import contract.InvalidRule;
import contract.RateLimiter;
import contract.UnknownClient;

import java.util.concurrent.ConcurrentHashMap;

final class ClientRateLimiter implements RateLimiter {
    private final Clock clock;
    private final ConcurrentHashMap<String, Limiter> clients = new ConcurrentHashMap<>();

    ClientRateLimiter(Clock clock) { this.clock = clock; }

    @Override
    public void configure(String clientId, Algorithm algorithm, int limit, long windowSeconds) {
        if (limit < 1 || windowSeconds < 1) throw new InvalidRule("limit=" + limit + " window=" + windowSeconds);
        clients.put(clientId, Limiters.create(algorithm, limit, windowSeconds, clock.now()));
    }

    @Override
    public boolean allow(String clientId) {
        Limiter l = clients.get(clientId);
        if (l == null) throw new UnknownClient(clientId);
        synchronized (l) {  // per-client lock
            return l.allow(clock.now());
        }
    }
}
