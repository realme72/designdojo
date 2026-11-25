package solution;

import contract.AlreadyParked;
import contract.Clock;
import contract.InvalidTicket;
import contract.LotFull;
import contract.ParkingLotApi;
import contract.Receipt;
import contract.SpotSize;
import contract.Ticket;
import contract.VehicleType;

import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Coordinates the gates: plate uniqueness, spot claim, ticket lifecycle.
 * Policies (allocation, pricing, time) are injected, so this class doesn't change when they do.
 */
final class ParkingLot implements ParkingLotApi {
    private record Session(Ticket ticket, Spot spot) {}

    private final SpotAllocator allocator;
    private final PricingPolicy pricing;
    private final Clock clock;
    private final Map<String, Session> active = new ConcurrentHashMap<>();
    private final Set<String> parkedPlates = ConcurrentHashMap.newKeySet();
    private final AtomicLong ticketSeq = new AtomicLong();

    ParkingLot(SpotAllocator allocator, PricingPolicy pricing, Clock clock) {
        this.allocator = allocator;
        this.pricing = pricing;
        this.clock = clock;
    }

    @Override
    public Ticket park(String plate, VehicleType type) {
        if (!parkedPlates.add(plate)) throw new AlreadyParked(plate);   // atomic reserve
        Spot spot;
        try {
            spot = allocator.claim(type).orElseThrow(() -> new LotFull("no spot for " + type));
        } catch (RuntimeException e) {
            parkedPlates.remove(plate);                                    // undo the reservation
            throw e;
        }
        Ticket ticket = new Ticket("T-" + ticketSeq.incrementAndGet(), plate, spot.floor(), spot.size(), spot.id(), clock.now());
        active.put(ticket.id(), new Session(ticket, spot));
        return ticket;
    }

    @Override
    public Receipt unpark(String ticketId) {
        Session s = ticketId == null ? null : active.remove(ticketId);   // atomic: only one caller wins
        if (s == null) throw new InvalidTicket(ticketId);
        long fee = pricing.feeCents(s.spot().size(), s.ticket().entryTime(), clock.now());
        allocator.release(s.spot());
        parkedPlates.remove(s.ticket().plate());
        return new Receipt(ticketId, fee);
    }

    @Override
    public int available(SpotSize size) {
        return allocator.free(size);
    }
}
