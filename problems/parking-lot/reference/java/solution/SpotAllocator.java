package solution;

import contract.SpotSize;
import contract.VehicleType;

import java.util.Optional;

/** Owns spot occupancy. Implementations must be thread-safe. */
interface SpotAllocator {
    /** Atomically claim a spot for this vehicle, or empty if none fits. */
    Optional<Spot> claim(VehicleType type);

    void release(Spot spot);

    int free(SpotSize size);
}
