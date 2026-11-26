package solution;

import contract.Clock;
import contract.RateLimiter;

public final class Solution {
    private Solution() {}

    public static RateLimiter create(Clock clock) {
        return new ClientRateLimiter(clock);
    }
}
