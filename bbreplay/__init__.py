from enum import Enum, auto


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


def prefix_for_teamtype(team_type):
    if team_type == TeamType.HOME:
        return "Home"
    elif team_type == TeamType.AWAY:
        return "Away"
    else:
        raise ValueError(f"No database table prefix for {team_type}")


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


# Based on dmchale's BBRR list from https://github.com/dmchale/BBRR/blob/master/classes/BBRRSkills.php
# and extended as new skills are found in replays
class Skills(Enum):
    STRIP_BALL = 1
    PLUS_1_MA = 4
    CATCH = 6
    DODGE = 7
    SPRINT = 8
    PASS_BLOCK = 9
    FOUL_APPEARANCE = 10
    LEAP = 11
    MIGHTY_BLOW = 13
    LEADER = 14
    HORNS = 15
    STAND_FIRM = 17
    REGENERATION = 19
    TAKE_ROOT = 20
    ACCURATE = 21
    BREAK_TACKLE = 22
    DAUNTLESS = 26
    DIRTY_PLAYER = 27
    DIVING_CATCH = 28
    DUMP_OFF = 29
    BLOCK = 30
    VERY_LONG_LEGS = 32
    DISTURBING_PRESENCE = 33
    DIVING_TACKLE = 34
    FEND = 35
    FRENZY = 36
    GRAB = 37
    GUARD = 38
    HAIL_MARY_PASS = 39
    JUGGERNAUT = 40
    JUMP_UP = 41
    LONER = 44
    NERVES_OF_STEEL = 45
    PASS = 47
    PREHENSILE_TAIL = 49
    PRO = 50
    REALLY_STUPID = 51
    RIGHT_STUFF = 52
    SECRET_WEAPON = 54
    SIDE_STEP = 56
    TACKLE = 57
    STRONG_ARM = 58
    STUNTY = 59
    SURE_FEET = 60
    THICK_SKULL = 63
    THROW_TEAMMATE = 64
    WILD_ANIMAL = 67
    WRESTLE = 68
    TENTACLES = 69
    MULTIPLE_BLOCK = 70
    KICK = 71
    CLAWS = 75
    STAB = 77
    HYPTNOTIC_GAZE = 78
    STAKES = 79
    BOMBARDIER = 80
    DECAY = 81
    NURGLES_ROT = 82


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
