from __future__ import annotations

from dataclasses import dataclass

from contract import Extra


@dataclass(frozen=True)
class DeliveryRule:
    penalty: int          # extra runs to the team on top of `runs`
    runs_to_batter: bool
    faced: bool           # does the striker face a ball?
    legal: bool           # counts toward the over?


RULES = {
    Extra.NONE: DeliveryRule(0, True, True, True),
    Extra.WIDE: DeliveryRule(1, False, False, False),
    Extra.NO_BALL: DeliveryRule(1, True, True, False),
    Extra.BYE: DeliveryRule(0, False, True, True),
    Extra.LEG_BYE: DeliveryRule(0, False, True, True),
}
