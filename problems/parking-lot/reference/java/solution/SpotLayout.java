package solution;

import contract.FloorConfig;
import contract.SpotSize;

import java.util.ArrayList;
import java.util.List;

/** Expands the floor config into concrete spots. */
final class SpotLayout {
    private SpotLayout() {}

    static List<Spot> from(List<FloorConfig> floors) {
        List<Spot> spots = new ArrayList<>();
        for (int f = 0; f < floors.size(); f++) {
            FloorConfig fc = floors.get(f);
            add(spots, f + 1, SpotSize.SMALL, fc.small());
            add(spots, f + 1, SpotSize.MEDIUM, fc.medium());
            add(spots, f + 1, SpotSize.LARGE, fc.large());
        }
        return spots;
    }

    private static void add(List<Spot> spots, int floor, SpotSize size, int count) {
        for (int i = 1; i <= count; i++) {
            spots.add(new Spot("F" + floor + "-" + size.name().charAt(0) + i, floor, size, i));
        }
    }
}
