# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from . import PlayerStatus, OFF_PITCH_POSITION


MA_TO_STAT = {
    17: 2,
    25: 3,
    33: 4,
    42: 5,
    50: 6,
    58: 7,
    67: 8,
    75: 9
}

AG_TO_STAT = {
    17: 1,
    33: 2,
    50: 3,
    67: 4,
    83: 5,
}

ST_TO_STAT = {
    30: 1,
    40: 2,
    50: 3,
    60: 4,
    70: 5,
    80: 6,
    90: 7
}

AV_TO_STAT = {
    28: 5,
    42: 6,
    58: 7,
    72: 8,
    83: 9,
    92: 10
}


class Positionable:
    def __init__(self):
        self.position = OFF_PITCH_POSITION

    def is_on_pitch(self):
        return not self.position.is_offpitch()


def create_player(team, number, name, move, strength, agility, armour_value, level, spp, value):
    try:
        # Use Float to handle "XX." values (nothing after the decimal point)
        # and round stats with int to keep the tables simple
        ma_stat = MA_TO_STAT[round(float(move))]
        st_stat = ST_TO_STAT[round(float(strength))]
        ag_stat = AG_TO_STAT[round(float(agility))]
        av_stat = AV_TO_STAT[round(float(armour_value))]
    except KeyError as ex:
        raise KeyError(f"Unhandled attribute value for {team.name} #{number} {name}") from ex
    return Player(number, name, ma_stat, st_stat, ag_stat, av_stat, level, spp, value, [])


class Player(Positionable):
    def __init__(self, number, name, move, strength, agility, armour_value, level, spp, value, skills):
        super().__init__()
        self.team = None
        self.number = number
        self.name = name
        self.MA = move
        self.ST = strength
        self.AG = agility
        self.AV = armour_value
        self.level = level
        self.SPP = spp
        self.value = value
        self.status = PlayerStatus.OKAY
        self.skills = skills

    def __repr__(self):
        return f"Player(number={self.number}, name={self.name}, " \
               f"level={self.level}, spp={self.SPP}, value={self.value}, {self.position})"
