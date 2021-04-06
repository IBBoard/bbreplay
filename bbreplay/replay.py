# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import sqlite3
from .teams import Team
from .command import create_command
from .log import parse_log_entries


class Replay:
    def __init__(self, db, log_entries):
        self.__db = db
        self.__log_entries = log_entries
        self.__commands = None
    
    def get_teams(self):
        cur = self.__db.cursor()
        cur.execute('SELECT team.strName, race.DATA_CONSTANT, iValue, iPopularity FROM Home_Team_Listing team INNER JOIN Home_Races race ON idRaces = race.ID')
        home_team = Team(*cur.fetchone(), self.__db)
        cur.execute('SELECT team.strName, race.DATA_CONSTANT, iValue, iPopularity FROM Away_Team_Listing team INNER JOIN Away_Races race ON idRaces = race.ID')
        away_team = Team(*cur.fetchone(), self.__db)
        cur.close()
        return home_team, away_team
    
    def get_commands(self):
        if not self.__commands:
            cur = self.__db.cursor()
            self.__commands = [create_command(self, row) for row in cur.execute('SELECT * FROM Replay_NetCommands ORDER BY ID')]
        return self.__commands


def load(db_path, log_path):
    db = sqlite3.connect(db_path)
    log_entries = parse_log_entries(log_path)
    return Replay(db, log_entries)
