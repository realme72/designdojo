package solution;

import contract.SpotSize;

/** How a stay is charged. New rules (weekend rates, EV surcharge) are new implementations. */
interface PricingPolicy {
    long feeCents(SpotSize size, long entryEpochSec, long exitEpochSec);
}
