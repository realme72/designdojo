package solution;

import contract.SpotSize;

import java.util.Comparator;

/** A physical spot. Immutable; occupancy is tracked by the allocator. */
record Spot(String id, int floor, SpotSize size, int index) {
    /** Lower floor first, then lower index: the allocation order within one size. */
    static final Comparator<Spot> BY_POSITION = Comparator.comparingInt(Spot::floor).thenComparingInt(Spot::index);
}
