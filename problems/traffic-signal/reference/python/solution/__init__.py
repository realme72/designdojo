from contract import Clock, SignalConfig, TrafficSignal

from .controller import Controller


def create(config: SignalConfig, clock: Clock) -> TrafficSignal:
    return Controller(config, clock)
