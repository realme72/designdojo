package solution;

import contract.SpotSize;
import contract.VehicleType;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/** Which spot sizes each vehicle type may use, smallest first. One table to edit for a new vehicle type. */
final class Compatibility {
    private final Map<VehicleType, List<SpotSize>> fits = new EnumMap<>(VehicleType.class);

    Compatibility() {
        fits.put(VehicleType.BIKE, List.of(SpotSize.SMALL, SpotSize.MEDIUM, SpotSize.LARGE));
        fits.put(VehicleType.CAR, List.of(SpotSize.MEDIUM, SpotSize.LARGE));
        fits.put(VehicleType.TRUCK, List.of(SpotSize.LARGE));
        fits.put(VehicleType.MOTORBIKE, List.of(SpotSize.SMALL));
    }

    List<SpotSize> sizesFor(VehicleType type) {
        List<SpotSize> sizes = fits.get(type);
        if (sizes == null) throw new IllegalArgumentException("no compatibility rule for " + type);
        return sizes;
    }
}
