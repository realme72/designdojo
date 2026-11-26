package solution;

import contract.SpotSize;

import java.util.EnumMap;
import java.util.Map;

/** Whole hours, rounded up, minimum one, at the spot size's rate. */
final class HourlyPricing implements PricingPolicy {
    private static final long HOUR = 3600;
    private final Map<SpotSize, Long> rateCents;

    HourlyPricing(Map<SpotSize, Long> rateCents) {
        this.rateCents = new EnumMap<>(rateCents);
        for (SpotSize s : SpotSize.values()) {
            if (!this.rateCents.containsKey(s)) throw new IllegalArgumentException("missing rate for " + s);
        }
    }

    static long hours(long entry, long exit) {
        long seconds = Math.max(0, exit - entry);
        return Math.max(1, (seconds + HOUR - 1) / HOUR);
    }

    long rate(SpotSize size) {
        return rateCents.get(size);
    }

    @Override
    public long feeCents(SpotSize size, long entry, long exit) {
        return hours(entry, exit) * rateCents.get(size);
    }
}
