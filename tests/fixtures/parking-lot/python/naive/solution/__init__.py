"""Deliberately naive: one god class, type switches, no locking, floor-rounded hours."""

from contract import (AlreadyParked, Clock, InvalidTicket, LotConfig, LotFull, ParkingLotApi, Receipt, SpotSize,
                      Ticket, VehicleType)


class Lot(ParkingLotApi):
    def __init__(self, config: LotConfig, clock: Clock):
        self.config, self.clock = config, clock
        self.spots = []  # [id, floor, size, occupied]
        for f, fc in enumerate(config.floors, start=1):
            for size, n in ((SpotSize.SMALL, fc.small), (SpotSize.MEDIUM, fc.medium), (SpotSize.LARGE, fc.large)):
                self.spots += [[f"{f}{size.name[0]}{i}", f, size, False] for i in range(n)]
        self.tickets = {}
        self.plates = {}
        self.counter = 0

    def park(self, plate, vehicle_type):
        if plate in self.plates:
            raise AlreadyParked()
        if vehicle_type == VehicleType.BIKE:
            sizes = [SpotSize.SMALL, SpotSize.MEDIUM, SpotSize.LARGE]
        elif vehicle_type == VehicleType.CAR:
            sizes = [SpotSize.MEDIUM, SpotSize.LARGE]
        else:
            sizes = [SpotSize.LARGE]
        for size in sizes:
            for s in self.spots:
                if s[2] == size and not s[3]:
                    s[3] = True
                    self.counter += 1
                    t = Ticket(f"T{self.counter}", plate, s[1], size, s[0], self.clock.now())
                    self.tickets[t.id] = (t, s, vehicle_type)
                    self.plates[plate] = t.id
                    return t
        raise LotFull()

    def unpark(self, ticket_id):
        if ticket_id not in self.tickets:
            raise InvalidTicket()
        t, s, vt = self.tickets[ticket_id]
        hours = max(1, (self.clock.now() - t.entry_time) // 3600)
        if vt == VehicleType.BIKE:
            rate = self.config.hourly_rate_cents[SpotSize.SMALL]
        elif vt == VehicleType.CAR:
            rate = self.config.hourly_rate_cents[SpotSize.MEDIUM]
        else:
            rate = self.config.hourly_rate_cents[SpotSize.LARGE]
        s[3] = False
        del self.plates[t.plate]
        del self.tickets[ticket_id]
        return Receipt(ticket_id, hours * rate)

    def available(self, size):
        return sum(1 for s in self.spots if s[2] == size and not s[3])


def create(config: LotConfig, clock: Clock) -> ParkingLotApi:
    return Lot(config, clock)
