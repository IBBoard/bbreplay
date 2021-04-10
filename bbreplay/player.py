# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from . import PlayerStatus, OFF_PITCH_POSITION


class Positionable:
    def __init__(self):
        self.position = OFF_PITCH_POSITION

    def is_on_pitch(self):
        return self.position != OFF_PITCH_POSITION


class Ball(Positionable):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return f"Ball({self.position})"


class Player(Positionable):
    def __init__(self, team, number, name, move, strength, agility, armour_value, level, spp, value):
        super().__init__()
        self.team = team
        self.number = number
        self.name = name
        # TODO: Convert stats
        self.MA = move
        self.ST = strength
        self.AG = agility
        self.AV = armour_value
        self.level = level
        self.SPP = spp
        self.value = value
        self.status = PlayerStatus.OKAY

    def __repr__(self):
        return f"Player(number={self.number}, name={self.name}, " \
               f"level={self.level}, spp={self.SPP}, value={self.value}, {self.position})"
