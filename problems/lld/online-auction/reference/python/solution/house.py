from __future__ import annotations

import threading
from dataclasses import dataclass, field

from contract import (AuctionClosed, AuctionHouse, AuctionOpen, AuctionResult, Bid, BidResult, BidTooLow, Clock,
                      DuplicateAuction, InvalidAuction, NoBids, SelfBid, UnknownAuction)


@dataclass
class Auction:
    id: str
    seller: str
    start: int
    increment: int
    ends_at: int
    bids: list[Bid] = field(default_factory=list)
    result: AuctionResult | None = None
    reserve: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def minimum_next(self) -> int:
        return self.bids[-1].amount + self.increment if self.bids else self.start


class House(AuctionHouse):
    def __init__(self, window: int, extension: int, clock: Clock):
        self._window, self._extension, self._clock = window, extension, clock
        self._auctions: dict[str, Auction] = {}
        self._lock = threading.Lock()

    def _auction(self, aid: str) -> Auction:
        with self._lock:
            a = self._auctions.get(aid)
        if a is None:
            raise UnknownAuction(aid)
        return a

    def create_auction(self, auction_id: str, seller: str, starting_price: int, min_increment: int,
                       ends_at: int) -> None:
        if starting_price < 1 or min_increment < 1 or ends_at <= self._clock.now():
            raise InvalidAuction(auction_id)
        with self._lock:
            if auction_id in self._auctions:
                raise DuplicateAuction(auction_id)
            self._auctions[auction_id] = Auction(auction_id, seller, starting_price, min_increment, ends_at)

    def bid(self, auction_id: str, bidder: str, amount: int) -> BidResult:
        a = self._auction(auction_id)
        with a.lock:  # validate + record atomically
            now = self._clock.now()
            rules = [
                (lambda: a.result is not None or now >= a.ends_at, AuctionClosed),
                (lambda: bidder == a.seller, SelfBid),
                (lambda: amount < a.minimum_next(), BidTooLow),
            ]
            for broken, error in rules:
                if broken():
                    raise error(auction_id)
            a.bids.append(Bid(bidder, amount))
            if a.ends_at - now < self._window:  # anti-sniping
                a.ends_at = now + self._extension
            return BidResult(amount, a.ends_at)

    def set_reserve(self, auction_id: str, reserve: int) -> None:
        a = self._auction(auction_id)
        with a.lock:
            if a.result is not None or self._clock.now() >= a.ends_at:
                raise AuctionClosed(auction_id)
            a.reserve = reserve

    def reserve_met(self, auction_id: str) -> bool:
        a = self._auction(auction_id)
        with a.lock:
            return bool(a.bids) and a.bids[-1].amount >= a.reserve

    def highest(self, auction_id: str) -> Bid:
        a = self._auction(auction_id)
        with a.lock:
            if not a.bids:
                raise NoBids(auction_id)
            return a.bids[-1]

    def history(self, auction_id: str) -> list[Bid]:
        a = self._auction(auction_id)
        with a.lock:
            return list(a.bids)

    def close(self, auction_id: str) -> AuctionResult:
        a = self._auction(auction_id)
        with a.lock:
            if a.result is None:
                if self._clock.now() < a.ends_at:
                    raise AuctionOpen(auction_id)
                top = a.bids[-1] if a.bids else None
                if top and top.amount < a.reserve:
                    top = None  # reserve not met: no sale
                a.result = AuctionResult(top.bidder if top else "", top.amount if top else 0)
            return a.result
