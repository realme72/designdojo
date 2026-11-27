package solution;

import contract.Broker;

public final class Solution {
    private Solution() {}

    public static Broker create() {
        return new InMemoryBroker();
    }
}
