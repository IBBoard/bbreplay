# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING
 
from enum import Enum


class TeamType(Enum):
    HOME = 0
    AWAY = 1
    HOTSEAT = -1


def player_idx_to_type(idx):
    if (idx > 1):
        return TeamType.HOTSEAT
    else:
        return TeamType(idx)


class Team:
    def __init__(self, name, race, team_value, fame, db):
        self.name = name
        self.race = race
        self.team_value = team_value
        self.fame = fame
        self.__db = db

    def get_players(self):
        pass
