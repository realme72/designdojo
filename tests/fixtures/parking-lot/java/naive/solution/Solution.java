package solution;

import contract.*;

import java.util.*;

/** Deliberately naive: one god class, type switches, no locking, floor-rounded hours. */
public final class Solution {
    private Solution() {}

    public static ParkingLotApi create(LotConfig config, Clock clock) {
        return new Lot(config, clock);
    }

    static final class Lot implements ParkingLotApi {
        final List<Object[]> spots = new ArrayList<>();   // {id, floor, size, occupied}
        final Map<String, Object[]> tickets = new HashMap<>();
        final Map<String, String> plates = new HashMap<>();
        final LotConfig config;
        final Clock clock;
        int counter = 0;

        Lot(LotConfig config, Clock clock) {
            this.config = config;
            this.clock = clock;
            for (int f = 0; f < config.floors().size(); f++) {
                FloorConfig fc = config.floors().get(f);
                for (int i = 0; i < fc.small(); i++) spots.add(new Object[]{f + "S" + i, f + 1, SpotSize.SMALL, false});
                for (int i = 0; i < fc.medium(); i++) spots.add(new Object[]{f + "M" + i, f + 1, SpotSize.MEDIUM, false});
                for (int i = 0; i < fc.large(); i++) spots.add(new Object[]{f + "L" + i, f + 1, SpotSize.LARGE, false});
            }
        }

        public Ticket park(String plate, VehicleType type) {
            if (plates.containsKey(plate)) throw new AlreadyParked();
            List<SpotSize> sizes;
            if (type == VehicleType.BIKE) sizes = List.of(SpotSize.SMALL, SpotSize.MEDIUM, SpotSize.LARGE);
            else if (type == VehicleType.CAR) sizes = List.of(SpotSize.MEDIUM, SpotSize.LARGE);
            else sizes = List.of(SpotSize.LARGE);
            for (SpotSize size : sizes) {
                for (Object[] s : spots) {
                    if (s[2] == size && !(Boolean) s[3]) {
                        s[3] = true;
                        counter++;
                        Ticket t = new Ticket("T" + counter, plate, (Integer) s[1], size, (String) s[0], clock.now());
                        tickets.put(t.id(), new Object[]{t, s, type});
                        plates.put(plate, t.id());
                        return t;
                    }
                }
            }
            throw new LotFull();
        }

        public Receipt unpark(String ticketId) {
            Object[] rec = tickets.get(ticketId);
            if (rec == null) throw new InvalidTicket();
            Ticket t = (Ticket) rec[0];
            long hours = Math.max(1, (clock.now() - t.entryTime()) / 3600);
            long rate;
            switch ((VehicleType) rec[2]) {
                case BIKE: rate = config.hourlyRateCents().get(SpotSize.SMALL); break;
                case CAR: rate = config.hourlyRateCents().get(SpotSize.MEDIUM); break;
                default: rate = config.hourlyRateCents().get(SpotSize.LARGE);
            }
            ((Object[]) rec[1])[3] = false;
            plates.remove(t.plate());
            tickets.remove(ticketId);
            return new Receipt(ticketId, hours * rate);
        }

        public int available(SpotSize size) {
            int n = 0;
            for (Object[] s : spots) if (s[2] == size && !(Boolean) s[3]) n++;
            return n;
        }
    }
}
