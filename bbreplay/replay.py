# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import sqlite3
from collections import namedtuple
from . import CoinToss, TeamType, PITCH_LENGTH, PITCH_WIDTH, TOP_ENDZONE_IDX, BOTTOM_ENDZONE_IDX, OFF_PITCH_POSITION
from .command import create_command, CoinTossCommand, RoleCommand, SetupCommand, SetupCompleteCommand, KickoffCommand
from .log import parse_log_entries, MatchLogEntry
from .teams import Team


MatchEvent = namedtuple('Match', [])
CoinTossEvent = namedtuple('CoinToss', ['toss_team', 'toss_choice', 'toss_result', 'role_team', 'role_choice'])
TeamSetupComplete = namedtuple('TeamSetupComplete', ['team', 'player_positions'])
SetupComplete = namedtuple('SetupComplete', ['board'])


class Replay:
    def __init__(self, db_path, log_path):
        self.__db = sqlite3.connect(db_path)
        cur = self.__db.cursor()
        cur.execute('SELECT team.strName, race.DATA_CONSTANT, iValue, iPopularity ' \
            'FROM Home_Team_Listing team INNER JOIN Home_Races race ON idRaces = race.ID')
        self.home_team = Team(*cur.fetchone(), TeamType.HOME, self.__db)
        cur.execute('SELECT team.strName, race.DATA_CONSTANT, iValue, iPopularity ' \
            'FROM Away_Team_Listing team INNER JOIN Away_Races race ON idRaces = race.ID')
        self.away_team = Team(*cur.fetchone(), TeamType.AWAY, self.__db)
        self.__commands = [create_command(self, row)
                           for row in cur.execute('SELECT * FROM Replay_NetCommands ORDER BY ID')]
        cur.close()
        self.__log_entries = parse_log_entries(log_path)
        
        log_entry = self.__log_entries[0]

        if type(log_entry) is not MatchLogEntry:
            raise ValueError("Log did not start with MatchLog entry")
        if log_entry.home_name != self.home_team.name:
            raise ValueError("Home team mismatch between replay and log")
        if log_entry.away_name != self.away_team.name:
            raise ValueError("Away team mismatch between replay and log")
        # TODO: More validation of matching

    def get_teams(self):
        return self.home_team, self.away_team
    
    def get_team(self, team_type):
        if team_type == TeamType.HOME:
            return self.home_team
        elif team_type == TeamType.AWAY:
            return self.away_team
        else:
            raise ValueError(f"Cannot get team for {team_type}")
    
    def events(self):
        log_entries = (log_entry for log_entry in self.__log_entries)
        cmds = (cmd for cmd in self.__commands)
        
        cmd = next(log_entries)
        yield MatchEvent()

        toss_cmd = find_next(cmd, cmds, CoinTossCommand)
        toss_log = next(log_entries)
        role_cmd = find_next(toss_cmd, cmds, RoleCommand)
        role_log = next(log_entries)
        if toss_cmd.team != toss_log.team or toss_cmd.choice != toss_log.choice:
            raise ValueError("Mistmatch in toss details")
        if role_cmd.team != role_log.team or role_cmd.choice != role_log.choice:
            raise ValueError("Mistmatch in role details")
        toss_choice = toss_cmd.choice
        if toss_cmd.team == role_cmd.team:
            toss_result = toss_choice
        elif toss_choice == CoinToss.HEADS:
            toss_result = CoinToss.TAILS
        else:
            toss_result = CoinToss.HEADS
        yield CoinTossEvent(toss_cmd.team, toss_choice, toss_result, role_cmd.team, role_cmd.choice)

        cmd = find_next(role_cmd, cmds, SetupCommand)

        board = [[None] * PITCH_WIDTH for _ in range(PITCH_LENGTH)]
        deployments_finished = 0
        team = None
        
        while True:
            cmd_type = type(cmd)
            if cmd_type is SetupCompleteCommand:
                deployments_finished += 1
                for i in range(PITCH_WIDTH):
                    endzone_contents = board[TOP_ENDZONE_IDX][i]
                    if endzone_contents:
                        board[TOP_ENDZONE_IDX][i] = None
                        endzone_contents.position = OFF_PITCH_POSITION
                    endzone_contents = board[BOTTOM_ENDZONE_IDX][i]
                    if endzone_contents:
                        board[BOTTOM_ENDZONE_IDX][i] = None
                        endzone_contents.position = OFF_PITCH_POSITION
                yield TeamSetupComplete(cmd.team, team.get_players())
                team = None
                if deployments_finished == 2:
                    yield SetupComplete(board)
                    break
                else:
                    cmd = next(cmds)
                    continue
            elif cmd_type is not SetupCommand:
                cmd = next(cmds)
                continue
            #else…

            if team is None:
                team = self.get_team(cmd.team)

            player = team.get_player(cmd.player_idx)
            if player.is_on_pitch():
                old_coords = player.position
                set_board_position(board, old_coords, None)
            else:
                old_coords = None
            
            coords = cmd.position
            space_contents = get_board_position(board, coords)

            if space_contents:
                if old_coords:
                    set_board_position(board, old_coords, space_contents)
                else:
                    space_contents.position = OFF_PITCH_POSITION

            set_board_position(board, coords, player)
            cmd = next(cmds)

    def get_commands(self):
        return self.__commands
    
    def get_log_entries(self):
        return self.__log_entries

def find_next(cur, generator, target_cls):
    while type(cur) is not target_cls:
        cur = next(generator)
    return cur

def set_board_position(board, position, value):
    board[position.y][position.x] = value
    if value:
        value.position = position

def get_board_position(board, position):
    return board[position.y][position.x]
