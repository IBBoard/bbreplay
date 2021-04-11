# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from . import PITCH_LENGTH, PITCH_WIDTH
from .player import Ball


class GameState:
    def __init__(self):
        self.__board = [[None] * PITCH_WIDTH for _ in range(PITCH_LENGTH)]
        self.__prone = set()
        self.__stupid = []

    def set_position(self, position, contents):
        self.__board[position.y][position.x] = contents
        if contents:
            contents.position = position

    def reset_position(self, position):
        self.set_position(position, None)

    def get_position(self, position):
        return self.__board[position.y][position.x]

    def __getitem__(self, idx):
        return self.__board[idx]

    def has_tacklezone(self, player):
        return player not in self.__prone and player not in self.__stupid

    def set_prone(self, player):
        self.__prone.add(player)

    def unset_prone(self, player):
        self.__prone.remove(player)

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
                if entity and not isinstance(entity, Ball):
                    entities.append(entity)
        return entities

