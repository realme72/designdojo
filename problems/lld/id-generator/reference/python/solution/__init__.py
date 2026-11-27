from contract import Clock, GeneratorConfig, IdGenerator

from .snowflake import Layout, Snowflake


def create(config: GeneratorConfig, clock: Clock) -> IdGenerator:
    return Snowflake(Layout(config.sequence_bits), config.epoch, config.worker_id, clock)
