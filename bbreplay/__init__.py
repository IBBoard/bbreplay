from enum import Enum


class BlockResult(Enum):
    PUSHED = 0
    DEFENDER_STUMBLES = 1
    DEFENDER_DOWN = 2
    BOTH_DOWN = 3
    ATTACKER_DOWN = 4


def block_string_to_enum(block_string):
    return BlockResult[block_string.upper().replace(' ', '_')]