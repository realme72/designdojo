package solution;

import contract.SpotSize;
import contract.VehicleType;

import java.util.Collection;
import java.util.EnumMap;
import java.util.Map;
import java.util.NavigableSet;
import java.util.Optional;
import java.util.TreeSet;

/**
 * Smallest compatible size first, then lowest floor.
 * One monitor guards all free sets: claims are O(log n) and short, so a single
 * lock is simpler than per-size locks and still never holds during pricing or I/O.
 */
final class SmallestFitAllocator implements SpotAllocator {
    private final Map<SpotSize, NavigableSet<Spot>> free = new EnumMap<>(SpotSize.class);
    private final Compatibility compatibility;

    SmallestFitAllocator(Collection<Spot> spots, Compatibility compatibility) {
        this.compatibility = compatibility;
        for (SpotSize s : SpotSize.values()) free.put(s, new TreeSet<>(Spot.BY_POSITION));
        for (Spot spot : spots) free.get(spot.size()).add(spot);
    }

    @Override
    public synchronized Optional<Spot> claim(VehicleType type) {
        for (SpotSize size : compatibility.sizesFor(type)) {
            Spot spot = free.get(size).pollFirst();
            if (spot != null) return Optional.of(spot);
        }
        return Optional.empty();
    }

    @Override
    public synchronized void release(Spot spot) {
        if (!free.get(spot.size()).add(spot)) {
            throw new IllegalStateException("spot released twice: " + spot.id());
        }
    }

    @Override
    public synchronized int free(SpotSize size) {
        return free.get(size).size();
    }
}
