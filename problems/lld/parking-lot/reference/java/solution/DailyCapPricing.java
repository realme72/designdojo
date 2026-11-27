package solution;

import contract.InvalidCap;
import contract.SpotSize;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Decorator: caps each 24-hour block (and the remainder) per spot size. */
final class DailyCapPricing implements PricingPolicy {
    private static final long DAY_HOURS = 24;
    private final HourlyPricing inner;
    private final Map<SpotSize, Long> caps = new ConcurrentHashMap<>();

    DailyCapPricing(HourlyPricing inner) {
        this.inner = inner;
    }

    void setCap(SpotSize size, long cap) {
        if (cap < 1) throw new InvalidCap("cap " + cap);
        caps.put(size, cap);
    }

    @Override
    public long feeCents(SpotSize size, long entry, long exit) {
        Long cap = caps.get(size);
        if (cap == null) return inner.feeCents(size, entry, exit);
        long hours = HourlyPricing.hours(entry, exit), rate = inner.rate(size);
        long days = hours / DAY_HOURS, rest = hours % DAY_HOURS;
        return days * Math.min(DAY_HOURS * rate, cap) + (rest > 0 ? Math.min(rest * rate, cap) : 0);
    }
}
