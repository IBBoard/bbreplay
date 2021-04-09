# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import sqlite3
from collections import namedtuple
from . import CoinToss, TeamType, ActionResult, \
    PITCH_LENGTH, PITCH_WIDTH, TOP_ENDZONE_IDX, BOTTOM_ENDZONE_IDX, OFF_PITCH_POSITION
from .command import *
from .log import parse_log_entries, MatchLogEntry, StupidEntry
from .player import Ball
from .teams import Team


MatchEvent = namedtuple('Match', [])
CoinTossEvent = namedtuple('CoinToss', ['toss_team', 'toss_choice', 'toss_result', 'role_team', 'role_choice'])
TeamSetupComplete = namedtuple('TeamSetupComplete', ['team', 'player_positions'])
SetupComplete = namedtuple('SetupComplete', ['board'])
Kickoff = namedtuple('Kickoff', ['target', 'scatter_direction', 'scatter_distance', 'bounces', 'ball', 'board'])
Block = namedtuple('Block', ['blocking_player', 'blocked_player', 'dice', 'result'])
Pushback = namedtuple('Pushback', ['pushing_player', 'pushed_player', 'source_space', 'taget_space', 'board'])
FollowUp = namedtuple('Followup', ['following_player', 'followed_player', 'source_space', 'target_space', 'board'])

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
        cmds = (cmd for cmd in self.__commands if not cmd.is_verbose)
        
        cmd = next(log_entries)
        yield MatchEvent()

        toss_cmd = find_next(cmds, CoinTossCommand)
        toss_log = next(log_entries)
        role_cmd = find_next(cmds, RoleCommand)
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

        cmd = find_next(cmds, SetupCommand)

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
                reset_board_position(board, old_coords)
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
        
        kickoff_cmd = find_next(cmds, KickoffCommand)
        kickoff_direction = next(log_entries)
        kickoff_scatter = next(log_entries)
        # TODO: Handle no bounce when it gets caught straight away
        kickoff_bounce = next(log_entries)
        # TODO: Handle second bounce for "Changing Weather" event rolling "Nice" again
        ball = Ball()
        ball_dest = kickoff_cmd.position.scatter(kickoff_direction.direction, kickoff_scatter.distance)\
                                        .scatter(kickoff_bounce.direction)
        set_board_position(board, ball_dest, ball)
        yield Kickoff(kickoff_cmd.position, kickoff_direction.direction, kickoff_scatter.distance,
                      [kickoff_bounce.direction], ball, board)

        while True:
            cmd = next(cmds)
            cmd_type = type(cmd)
            if isinstance(cmd, TargetPlayerCommand):
                target = cmd
                target_by_idx = self.get_team(target.target_team).get_player(target.target_player)
                log_entry = next(log_entries)
                if isinstance(log_entry, StupidEntry):
                    if log_entry.result == ActionResult.SUCCESS:
                        log_entry = next(log_entries)
                    else:
                        # The stupid stopped us
                        continue

                cmd = next(cmds)
                if isinstance(cmd, BlockCommand):
                    block = cmd
                    blocking_player = self.get_team(block.team).get_player(block.player_idx)
                    block_dice = log_entry
                    # TODO: Handle cmd_type=20 (reroll?)
                    block_choice = next(cmds)
                    target_by_coords = get_board_position(board, block.position)
                    if target_by_coords != target_by_idx:
                        raise ValueError(f"{target} targetted {target_by_idx} but {block} targetted {target_by_coords}")
                    yield Block(blocking_player, target_by_idx,
                                block_dice.results, block_dice.results[block_choice.dice_idx])
                    block_result = next(cmds)
                    if isinstance(block_result, PushbackCommand):
                        old_coords = block.position
                        reset_board_position(board, old_coords)
                        set_board_position(board, block_result.position, target_by_coords)
                        yield Pushback(blocking_player, target_by_idx, old_coords, block_result.position, board)
                        block_result = next(cmds)
                    # Follow-up
                    if block_result.choice:
                        old_coords = blocking_player.position
                        reset_board_position(board, old_coords)
                        set_board_position(board, block.position, blocking_player)
                        yield FollowUp(blocking_player, target_by_idx, old_coords, block.position, board)

            elif cmd_type is Command or cmd_type is PreKickoffCompleteCommand:
                continue
            elif cmd_type is EndTurnCommand:
                break


    def get_commands(self):
        return self.__commands
    
    def get_log_entries(self):
        return self.__log_entries


def find_next(generator, target_cls):
    while True:
        cur = next(generator)
        if isinstance(cur, target_cls):
            break
    return cur

def reset_board_position(board, position):
    set_board_position(board, position, None)

def set_board_position(board, position, value):
    board[position.y][position.x] = value
    if value:
        value.position = position

def get_board_position(board, position):
    return board[position.y][position.x]
