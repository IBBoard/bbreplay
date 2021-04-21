# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import xml.etree.ElementTree as ET
from . import prefix_for_teamtype
from .player import Player


class Team:
    def __init__(self, name, race, team_value, fame, rerolls, team_type, db):
        self.name = name
        self.race = race
        self.team_value = team_value
        self.fame = fame
        self.rerolls = rerolls
        self.team_type = team_type
        self._db = db
        self._players = []
        self._player_number_map = {}

        table_prefix = prefix_for_teamtype(self.team_type)

        cur = self._db.cursor()
        cur.execute('SELECT Match_strSave FROM SavedGameInfo')
        xml_str = cur.fetchone()[0]
        match_xml = ET.fromstring(xml_str)
        player_numbers = match_xml.findall(f'.//{table_prefix}/vecPlayersInit/*/Number')
        for i, num in enumerate(player_numbers):
            self._player_number_map[int(num.text)] = i
        self._players = [None] * len(self._player_number_map)

        player_rows = cur.execute('SELECT ID, iNumber, strName, '
                                  'Characteristics_fMovementAllowance, Characteristics_fStrength, '
                                  'Characteristics_fAgility, Characteristics_fArmourValue, '
                                  'idPlayer_Levels, iExperience, iValue '
                                  f'FROM {table_prefix}_Player_Listing')

        for row in player_rows:
            player = Player(self, *row, db)
            idx = self._player_number_map[player.number]
            self._players[idx] = player

    def get_players(self):
        return self._players

    def get_player(self, idx):
        return self._players[idx]

    def get_player_by_number(self, number):
        idx = self._player_number_map[int(number)]
        return self._players[idx]
