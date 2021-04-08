# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING
 
from . import PlayerStatus, Position, OFF_PITCH_POSITION


class Player:
    def __init__(self, team, number, name, move, strength, agility, armour_value, level, spp, value):
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
        self.position = OFF_PITCH_POSITION
        self.status = PlayerStatus.OKAY
    
    def is_on_pitch(self):
        return self.position != OFF_PITCH_POSITION

    def __repr__(self):
        return f"Player(number={self.number}, name={self.name}, " \
               f"level={self.level}, spp={self.SPP}, value={self.value}, {self.position})"
    