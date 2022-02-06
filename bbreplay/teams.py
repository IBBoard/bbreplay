# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from enum import Enum
import xml.etree.ElementTree as ET
from . import prefix_for_teamtype, Skills
from .player import create_player


MAX_PLAYER_COUNT = 16


class CoachType(Enum):
    LOCAL = 0
    AI = 1
    REMOTE = 2


def create_team(db, team_type):
    table_prefix = prefix_for_teamtype(team_type)
    cur = db.cursor()
    cur.execute('SELECT Match_strSave FROM SavedGameInfo')
    xml_str = cur.fetchone()[0]
    match_xml = ET.fromstring(xml_str)
    coach_type = CoachType(int(match_xml.find(f'.//{table_prefix}/ePlayerType').text))
    cur.execute('SELECT team.strName, race.DATA_CONSTANT, iValue, iPopularity, iRerolls, bApothecary '
                f'FROM {table_prefix}_Team_Listing team INNER JOIN {table_prefix}_Races race ON idRaces = race.ID')
    team = Team(*cur.fetchone(), team_type, coach_type)
    player_numbers = match_xml.findall(f'.//{table_prefix}/vecPlayersInit/*/Number')
    player_number_map = {}
    for i, num in enumerate(player_numbers):
        player_number_map[int(num.text)] = i

    player_rows = cur.execute('SELECT ID, iNumber, strName, '
                              'Characteristics_fMovementAllowance, Characteristics_fStrength, '
                              'Characteristics_fAgility, Characteristics_fArmourValue, '
                              'idPlayer_Levels, iExperience, iValue '
                              f'FROM {table_prefix}_Player_Listing')
    player_cache = {}
    for row in player_rows:
        player = create_player(team, *row[1:])
        player_cache[row[0]] = player
        team.add_player(player_number_map[player.number], player)

    type_skills = cur.execute('SELECT player.ID, idSkill_Listing, description '
                              f'FROM {table_prefix}_Player_Listing player '
                              f'INNER JOIN {table_prefix}_Player_Type_Skills type_skills '
                              'ON player.idPlayer_Types = type_skills.idPlayer_Types')

    for skill_row in type_skills:
        player = player_cache[skill_row[0]]
        try:
            player.skills.append(Skills(skill_row[1]))
        except ValueError as ex:
            raise ValueError(f"Unidentified skill {skill_row[1]} ({skill_row[2]}) for {team.name} player "
                             f"#{player.number} {player.name}") from ex

    learned_skills = cur.execute(f'SELECT idPlayer_Listing, idSkill_Listing FROM {table_prefix}_Player_Skills')

    for skill_row in learned_skills:
        player = player_cache[skill_row[0]]
        try:
            player.skills.append(Skills(skill_row[1]))
        except ValueError as ex:
            raise ValueError(f"Unidentified learned skill {skill_row[1]} for {team.name} player "
                             f"#{player.number} {player.name}") from ex

    cur.close()
    return team


class Team:
    def __init__(self, name, race, team_value, fame, rerolls, apothecary, team_type, coach_type=CoachType.AI):
        self.name = name
        self.race = race
        self.team_value = team_value
        self.fame = fame
        self.rerolls = rerolls
        self.apothecaries = apothecary
        self.team_type = team_type
        self._players = [None] * MAX_PLAYER_COUNT
        self._player_number_map = {}
        self.coach_type = coach_type

    def add_player(self, idx, player):
        self._player_number_map[player.number] = idx
        self._players[idx] = player
        player.team = self

    def get_players(self):
        return filter(None, self._players)

    def get_player(self, idx):
        return self._players[idx]

    def get_player_by_number(self, number):
        idx = self._player_number_map[int(number)]
        return self._players[idx]

    def get_player_number(self, idx):
        return self._players[idx].number
