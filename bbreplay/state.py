# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from collections import namedtuple
from . import other_team, Role, PITCH_LENGTH, PITCH_WIDTH, OFF_PITCH_POSITION

EndTurn = namedtuple('EndTurn', ['team', 'number', 'reason', 'board'])
StartTurn = namedtuple('StartTurn', ['team', 'number', 'board'])

class GameState:
    def __init__(self, home_team, away_team):
        self.__teams = [home_team, away_team]
        self.turn_team = None
        self.__board = [[None] * PITCH_WIDTH for _ in range(PITCH_LENGTH)]
        self.__turn = 0
        self.__prone = set()
        self.__stupid = set()
        self.__ball_position = OFF_PITCH_POSITION
        self.__ball_carrier = None

    @property
    def turn(self):
        return self.__turn // 2 + 1

    def start_match(self, role_team, role_choice):
        starting_team = role_team if role_choice == Role.RECEIVE else other_team(role_team)
        self.turn_team = self.__teams[starting_team.value]
        return StartTurn(starting_team, self.turn, self)

    def end_turn(self, team, reason):
        yield EndTurn(team, self.turn, reason, self)
        self.__turn += 1
        next_team = other_team(team)
        self.turn_team = self.__teams[next_team.value]
        yield StartTurn(next_team, self.turn, self)

    def set_position(self, position, contents):
        self.__board[position.y][position.x] = contents
        if contents:
            contents.position = position

    def reset_position(self, position):
        self.set_position(position, None)

    def get_position(self, position):
        return self.__board[position.y][position.x]

    def set_ball_position(self, position):
        self.__ball_carrier = None
        self.__ball_position = position

    def set_ball_carrier(self, player):
        self.__ball_carrier = player

    def get_ball_position(self):
        if self.__ball_carrier:
            return self.__ball_carrier.position
        else:
            return self.__ball_position

    def get_ball_carrier(self):
        return self.__ball_carrier

    def __getitem__(self, idx):
        return self.__board[idx]

    def has_tacklezone(self, player):
        return not self.is_prone(player) and player not in self.__stupid

    def set_prone(self, player):
        self.__prone.add(player)

    def unset_prone(self, player):
        self.__prone.remove(player)

    def is_prone(self, player):
        return player in self.__prone

    def get_surrounding_players(self, position):
        entities = []
        for i in [-1, 0, 1]:
            x = position.x + i
            if x < 0 or x >= PITCH_WIDTH:
                continue
            for j in [-1, 0, 1]:
                y = position.y + j
                if y < 0 or y >= PITCH_LENGTH:
                    continue
                if i == 0 and j == 0:
                    continue
                entity = self.__board[y][x]
                if entity:
                    entities.append(entity)
        return entities

