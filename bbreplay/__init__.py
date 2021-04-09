from enum import Enum, Flag, auto


class BlockResult(Enum):
    PUSHED = 0
    DEFENDER_STUMBLES = 1
    DEFENDER_DOWN = 2
    BOTH_DOWN = 3
    ATTACKER_DOWN = 4


class CoinToss(Enum):
    HEADS = 1
    TAILS = 0


class Role(Enum):
    KICK = 0
    RECEIVE = 1


class TeamType(Enum):
    HOME = 0
    AWAY = 1
    HOTSEAT = -1


class ActionResult(Enum):
    SUCCESS = 0
    FAILURE = 1


class ScatterDirection(Enum):
    NW = 1
    N = 2
    NE = 3
    W = 4
    E = 5
    SW = 6
    S = 7
    SE = 8


_wests = [ScatterDirection.NW, ScatterDirection.W, ScatterDirection.SW]
_easts = [ScatterDirection.NE, ScatterDirection.E, ScatterDirection.SE]
_norths = [ScatterDirection.NW, ScatterDirection.N, ScatterDirection.NE]
_souths = [ScatterDirection.SW, ScatterDirection.S, ScatterDirection.SE]


class PlayerStatus(Enum):
    OKAY = auto()
    PRONE = auto()
    STUNNED = auto()
    STUPID = auto()


class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def scatter(self, direction, distance=1):
        global _wests, _easts, _norths, _souths

        new_x = self.x
        if direction in _wests:
            new_x -= distance
        elif direction in _easts:
            new_x += distance

        new_y = self.y
        if direction in _norths:
            new_y += distance
        elif direction in _souths:
            new_y -= distance

        return Position(new_x, new_y)
    
    def __repr__(self):
        return f"Position({self.x}, {self.y})"


OFF_PITCH_POSITION = Position(-1, -1)

PITCH_LENGTH = 26
PITCH_WIDTH = 15
WIDEZONE_WIDTH = 4
TOP_ENDZONE_IDX = 0
BOTTOM_ENDZONE_IDX = PITCH_LENGTH - 1
LAST_COLUMN_IDX = PITCH_WIDTH - 1
LEFT_WIDEZONE_IDX = WIDEZONE_WIDTH - 1
RIGHT_WIDEZONE_IDX = PITCH_WIDTH - WIDEZONE_WIDTH
AFTER_HALFWAY_IDX = PITCH_LENGTH // 2
BEFORE_HALFWAY_IDX = AFTER_HALFWAY_IDX - 1


def player_idx_to_type(idx):
    if (idx > 1):
        return TeamType.HOTSEAT
    else:
        return TeamType(idx)


def block_string_to_enum(block_string):
    return BlockResult[block_string.upper().replace(' ', '_')]