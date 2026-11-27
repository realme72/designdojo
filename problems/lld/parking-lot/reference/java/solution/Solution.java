package solution;

import contract.Clock;
import contract.LotConfig;
import contract.ParkingLotApi;

/** Composition root: the only place that knows which concrete policies are used. */
public final class Solution {
    private Solution() {}

    public static ParkingLotApi create(LotConfig config, Clock clock) {
        SpotAllocator allocator = new SmallestFitAllocator(SpotLayout.from(config.floors()), new Compatibility());
        DailyCapPricing pricing = new DailyCapPricing(new HourlyPricing(config.hourlyRateCents()));
        return new ParkingLot(allocator, pricing, clock);
    }
}
