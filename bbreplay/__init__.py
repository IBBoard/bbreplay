# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

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


class ThrowResult(Enum):
    FUMBLE = auto()
    INACCURATE_PASS = auto()
    ACCURATE_PASS = auto()


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


class ThrowInDirection(Enum):
    DOWN_PITCH = 1
    CENTRE = 2
    UP_PITCH = 3


class PlayerStatus(Enum):
    OKAY = auto()
    PRONE = auto()
    STUNNED = auto()
    STUPID = auto()


class InjuryRollResult(Enum):
    STUNNED = auto()
    KO = auto()
    INJURED = auto()


class CasualtyResult(Enum):
    NONE = -1
    BADLY_HURT = 0
    BROKEN_RIBS = 1
    GROIN_STRAIN = 2
    GOUGED_EYE = 3
    BROKEN_JAW = 4
    FRACTURED_ARM = 5
    FRACTURED_LEG = 6
    SMASHED_HAND = 7
    PINCHED_NERVE = 8
    DAMAGED_BACK = 9
    SMASHED_KNEE = 10
    SMASHED_HIP = 11
    SMASHED_ANKLE = 12
    SERIOUS_CONCUSSION = 13
    FRACTURED_SKULL = 14
    BROKEN_NECK = 15
    SMASHED_COLLAR_BONE = 16
    DEAD = 17


class KickoffEvent(Enum):
    GET_THE_REF = 2
    RIOT = 3
    PERFECT_DEFENCE = 4
    HIGH_KICK = 5
    CHEERING_FANS = 6
    CHANGING_WEATHER = 7
    BRILLIANT_COACHING = 8
    QUICK_SNAP = 9
    BLITZ = 10
    THROW_A_ROCK = 11
    PITCH_INVASION = 12


class Weather(Enum):
    SWELTERING_HEAT = auto()
    VERY_SUNNY = auto()
    NICE = auto()
    NICE_BOUNCY = auto()  # Nice from a "Changing Weather" roll
    POURING_RAIN = auto()
    BLIZZARD = auto()


# Based on dmchale's BBRR list from https://github.com/dmchale/BBRR/blob/master/classes/BBRRSkills.php
# and extended as new skills are found in replays
class Skills(Enum):
    STRIP_BALL = 1
    PLUS_1_ST = 2
    PLUS_1_AG = 3
    PLUS_1_MA = 4
    PLUS_1_AV = 5
    CATCH = 6
    DODGE = 7
    SPRINT = 8
    PASS_BLOCK = 9
    FOUL_APPEARANCE = 10
    LEAP = 11
    EXTRA_ARM = 12
    MIGHTY_BLOW = 13
    LEADER = 14
    HORNS = 15
    STAND_FIRM = 17
    ALWAYS_HUNGRY = 18
    REGENERATION = 19
    TAKE_ROOT = 20
    ACCURATE = 21
    BREAK_TACKLE = 22
    SNEAKY_GIT = 23
    CHAINSAW = 25
    DAUNTLESS = 26
    DIRTY_PLAYER = 27
    DIVING_CATCH = 28
    DUMP_OFF = 29
    BLOCK = 30
    BONE_HEAD = 31
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
    NO_HANDS = 46
    PASS = 47
    PREHENSILE_TAIL = 49
    PRO = 50
    REALLY_STUPID = 51
    RIGHT_STUFF = 52
    SAFE_THROW = 53
    SECRET_WEAPON = 54
    SIDE_STEP = 56
    TACKLE = 57
    STRONG_ARM = 58
    STUNTY = 59
    SURE_FEET = 60
    SURE_HANDS = 61
    THICK_SKULL = 63
    THROW_TEAMMATE = 64
    WILD_ANIMAL = 67
    WRESTLE = 68
    TENTACLES = 69
    MULTIPLE_BLOCK = 70
    KICK = 71
    KICKOFF_RETURN = 72
    CLAWS = 75
    BALL_AND_CHAIN = 76
    STAB = 77
    HYPTNOTIC_GAZE = 78
    STAKES = 79
    BOMBARDIER = 80
    DECAY = 81
    NURGLES_ROT = 82
    TITCHY = 83


class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.__offpitch = x < 0 or x >= PITCH_WIDTH or y < 0 or y >= PITCH_LENGTH

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

    def throwin(self, direction, distance):
        dx = distance if self.x == 0 else -distance
        dy = (direction.value - 2) * distance
        return self.add(dx, dy)

    def add(self, dx, dy):
        return Position(self.x + dx, self.y + dy)

    def invert(self):
        if self == OFF_PITCH_POSITION:
            return OFF_PITCH_POSITION
        else:
            return Position(LAST_COLUMN_IDX - self.x, FAR_ENDZONE_IDX - self.y)

    def is_offpitch(self):
        return self.__offpitch

    def __eq__(self, other):
        if not other:
            return False
        elif type(other) != type(self):
            return False
        else:
            return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Position({self.x}, {self.y})"


class Peekable:
    def __init__(self, iterable):
        self._generator = (item for item in iterable)
        self._peeked = None

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        to_return = self._peeked
        self._peeked = None
        if to_return is None:
            to_return = next(self._generator)
        return to_return

    def peek(self):
        if self._peeked is None:
            self._peeked = next(self._generator, None)
        return self._peeked


OFF_PITCH_POSITION = Position(-1, -1)

PITCH_LENGTH = 26
PITCH_WIDTH = 15
WIDEZONE_WIDTH = 4
NEAR_ENDZONE_IDX = 0
FAR_ENDZONE_IDX = PITCH_LENGTH - 1
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


def enum_name_to_enum(enum_name, enum_type):
    return enum_type[enum_name.upper().replace(' ', '_')]


def other_team(team):
    return TeamType.AWAY if team == TeamType.HOME else TeamType.HOME
