# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import sqlite3
from collections import namedtuple
from . import CoinToss, TeamType, ActionResult, BlockResult, Skills, \
    PITCH_LENGTH, PITCH_WIDTH, TOP_ENDZONE_IDX, BOTTOM_ENDZONE_IDX, OFF_PITCH_POSITION
from .command import *
from .log import parse_log_entries, MatchLogEntry, StupidEntry, DodgeEntry, DodgeSkillEntry, ArmourValueRollEntry, \
    PickupEntry, TentacledEntry
from .player import Ball
from .state import GameState
from .teams import Team


MatchEvent = namedtuple('Match', [])
CoinTossEvent = namedtuple('CoinToss', ['toss_team', 'toss_choice', 'toss_result', 'role_team', 'role_choice'])
TeamSetupComplete = namedtuple('TeamSetupComplete', ['team', 'player_positions'])
SetupComplete = namedtuple('SetupComplete', ['board'])
Kickoff = namedtuple('Kickoff', ['target', 'scatter_direction', 'scatter_distance', 'bounces', 'ball', 'board'])
Movement = namedtuple('Movement', ['player', 'source_space', 'target_space', 'board'])
FailedMovement = namedtuple('FailedMovement', ['player', 'source_space', 'target_space'])
Block = namedtuple('Block', ['blocking_player', 'blocked_player', 'dice', 'result'])
Blitz = namedtuple('Blitz', ['blitzing_player', 'blitzed_player'])
DodgeBlock = namedtuple('DodgeBlock', ['blocking_player', 'blocked_player'])
Pushback = namedtuple('Pushback', ['pushing_player', 'pushed_player', 'source_space', 'taget_space', 'board'])
FollowUp = namedtuple('Followup', ['following_player', 'followed_player', 'source_space', 'target_space', 'board'])
ArmourRoll = namedtuple('ArmourRoll', ['player', 'result'])
Dodge = namedtuple('Dodge', ['player', 'result'])
Pickup = namedtuple('Pickup', ['player', 'position', 'result'])
PlayerDown = namedtuple('PlayerDown', ['player'])
ConditionCheck = namedtuple('ConditionCheck', ['player', 'condition', 'result'])
Tentacle = namedtuple('Tentacle', ['dodging_player', 'tentacle_player', 'result'])
Reroll = namedtuple('Reroll', ['team'])
EndTurn = namedtuple('EndTurn', ['team', 'number', 'board'])


class Replay:
    def __init__(self, db_path, log_path):
        self.__db = sqlite3.connect(db_path)
        cur = self.__db.cursor()
        cur.execute('SELECT team.strName, race.DATA_CONSTANT, iValue, iPopularity '
                    'FROM Home_Team_Listing team INNER JOIN Home_Races race ON idRaces = race.ID')
        self.home_team = Team(*cur.fetchone(), TeamType.HOME, self.__db)
        cur.execute('SELECT team.strName, race.DATA_CONSTANT, iValue, iPopularity '
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
            raise ValueError("Home team mismatch between replay and log - got "
                             f"{log_entry.home_name} expected {self.home_team.name}")
        if log_entry.away_name != self.away_team.name:
            raise ValueError("Away team mismatch between replay and log - got "
                             f"{log_entry.away_name} expected {self.away_team.name}")
        # TODO: More validation of matching

        self.__generator = self.__default_generator

    def get_teams(self):
        return self.home_team, self.away_team

    def get_team(self, team_type):
        if team_type == TeamType.HOME:
            return self.home_team
        elif team_type == TeamType.AWAY:
            return self.away_team
        else:
            raise ValueError(f"Cannot get team for {team_type}")

    def __default_generator(self, data):
        yield from data

    def set_generator(self, generator):
        if generator:
            self.__generator = generator
        else:
            self.__generator = self.__default_generator

    def events(self):
        log_entries = self.__generator(log_entry for log_entry in self.__log_entries)
        cmds = self.__generator(cmd for cmd in self.__commands if not cmd.is_verbose)

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

        board = GameState()
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
            # else…

            if team is None:
                team = self.get_team(cmd.team)

            player = team.get_player(cmd.player_idx)
            if player.is_on_pitch():
                old_coords = player.position
                board.reset_position(old_coords)
            else:
                old_coords = None

            coords = cmd.position
            space_contents = board.get_position(coords)

            if space_contents:
                if old_coords:
                    board.set_position(old_coords, space_contents)
                else:
                    space_contents.position = OFF_PITCH_POSITION

            board.set_position(coords, player)
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
        board.set_position(ball_dest, ball)
        yield Kickoff(kickoff_cmd.position, kickoff_direction.direction, kickoff_scatter.distance,
                      [kickoff_bounce.direction], ball, board)

        turn = 0

        while True:
            cmd = next(cmds, None)
            if cmd is None:
                break
            cmd_type = type(cmd)
            if isinstance(cmd, TargetPlayerCommand):
                target = cmd
                targeting_player = self.get_team(target.team).get_player(target.player_idx)
                target_by_idx = self.get_team(target.target_team).get_player(target.target_player)
                if Skills.REALLY_STUPID in targeting_player.skills:
                    log_entry = next(log_entries)
                    validate_log_entry(log_entry, StupidEntry, target.team, targeting_player.number)
                    yield ConditionCheck(targeting_player, 'Really Stupid', log_entry.result)
                    if log_entry.result != ActionResult.SUCCESS:
                        # The stupid stopped us
                        continue

                cmd = next(cmds)
                if isinstance(cmd, MovementCommand):
                    yield Blitz(targeting_player, target_by_idx)
                    cmd, actions = self.__process_movement(targeting_player, cmd, cmds, log_entries, board)
                    yield from actions
                if isinstance(cmd, BlockCommand):
                    block = cmd
                    blocking_player = targeting_player
                    block_dice = next(log_entries)
                    block_choice = next(cmds)
                    if isinstance(block_choice, RerollCommand):
                        reroll = next(log_entries)
                        yield Reroll(reroll.team)
                        block_dice = next(log_entries)
                        block_choice = next(cmds)
                    target_by_coords = board.get_position(block.position)
                    if target_by_coords != target_by_idx:
                        raise ValueError(f"{target} targetted {target_by_idx} but {block} targetted {target_by_coords}")
                    chosen_block_dice = block_dice.results[block_choice.dice_idx]
                    yield Block(blocking_player, target_by_idx,
                                block_dice.results, chosen_block_dice)
                    block_result = next(cmds)
                    if isinstance(block_result, PushbackCommand):
                        old_coords = block.position
                        board.reset_position(old_coords)
                        board.set_position(block_result.position, target_by_coords)
                        yield Pushback(blocking_player, target_by_idx, old_coords, block_result.position, board)
                        block_result = next(cmds)
                    # Follow-up
                    if block_result.choice:
                        old_coords = blocking_player.position
                        board.reset_position(old_coords)
                        board.set_position(block.position, blocking_player)
                        yield FollowUp(blocking_player, target_by_idx, old_coords, block.position, board)

                    if chosen_block_dice == BlockResult.DEFENDER_DOWN \
                        or chosen_block_dice == BlockResult.DEFENDER_STUMBLES \
                        or chosen_block_dice == BlockResult.BOTH_DOWN:
                        armour_entry = next(log_entries)
                        if isinstance(armour_entry, DodgeSkillEntry):
                            yield DodgeBlock(blocking_player, target_by_idx)
                        else:
                            validate_log_entry(armour_entry, ArmourValueRollEntry,
                                               target.target_team, target_by_idx.number)
                            board.set_prone(target_by_idx)
                            yield PlayerDown(target_by_idx)
                            yield ArmourRoll(target_by_idx, armour_entry.result)
            elif isinstance(cmd, MovementCommand):
                player = self.get_team(cmd.team).get_player(cmd.player_idx)
                if Skills.REALLY_STUPID in player.skills:
                    log_entry = next(log_entries)
                    validate_log_entry(log_entry, StupidEntry, cmd.team, player.number)
                    yield ConditionCheck(player, 'Really Stupid', log_entry.result)
                    if log_entry.result != ActionResult.SUCCESS:
                        # The stupid stopped us
                        continue
                # We stop when the movement stops, so the returned command is the EndMovementCommand
                _, actions = self.__process_movement(player, cmd, cmds, log_entries, board)
                yield from actions
            elif cmd_type is Command or cmd_type is PreKickoffCompleteCommand:
                continue
            elif cmd_type is EndTurnCommand:
                turn += 1
                yield EndTurn(cmd.team, turn // 2 + 1, board)
            else:
                print(f"No handling for {cmd}")
                break

    def get_commands(self):
        return self.__commands

    def get_log_entries(self):
        return self.__log_entries


    def __process_movement(self, player, cmd, cmds, log_entries, board):
        events = []
        failed_movement = False
        pickup_entry = None
        start_space = player.position
        while True:
            movement = cmd
            target_space = movement.position
            if not failed_movement:
                if is_dodge(board, player, target_space):
                    while True:
                        log_entry = next(log_entries)
                        if isinstance(log_entry, DodgeEntry):
                            validate_log_entry(log_entry, DodgeEntry, player.team.team_type, player.number)
                            events.append(Dodge(player, log_entry.result))
                        elif isinstance(log_entry, TentacledEntry):
                            validate_log_entry(log_entry, TentacledEntry, player.team.team_type, player.number)
                            attacker = self.get_team(log_entry.attacking_team)\
                                           .get_player_by_number(log_entry.attacking_player)
                            events.append(Tentacle(player, attacker, log_entry.result))
                        else:
                            raise ValueError("Looking for dodge-related log entries but got "
                                             f"{type(log_entry)}")
                        # TODO: Handle dodge failing and going splat
                        if log_entry.result != ActionResult.SUCCESS:
                            failed_movement = True
                            break

            target_contents = board.get_position(target_space)
            if target_contents:
                if isinstance(target_contents, Ball):
                    log_entry = next(log_entries)
                    validate_log_entry(log_entry, PickupEntry, player.team.team_type, player.number)
                    pickup_entry = log_entry
                elif target_contents == player:
                    # It's a stand-up in the same space
                    board.unset_prone(player)
                    pass
                else:
                    raise ValueError(f"{player} tried to move to occupied space {target_space}")

            if not failed_movement:
                board.reset_position(start_space)
                board.set_position(target_space, player)
                events.append(Movement(player, start_space, target_space, board))
            else:
                events.append(FailedMovement(player, start_space, target_space))

            if pickup_entry:
                events.append(Pickup(player, movement.position, pickup_entry.result))
                if pickup_entry.result != ActionResult.SUCCESS:
                    failed_movement = True
                pickup_entry = None

            start_space = target_space

            if type(cmd) is EndMovementCommand:
                break
            cmd = next(cmds)
            if not isinstance(cmd, MovementCommand):
                break

        return cmd, events


def find_next(generator, target_cls):
    while True:
        cur = next(generator)
        if isinstance(cur, target_cls):
            break
    return cur


def is_dodge(board, player, destination):
    if player.position == destination:
        return False
    else:
        entities = board.get_surrounding_players(player.position)
        return any(entity.team != player.team and board.has_tacklezone(entity) for entity in entities)


def validate_log_entry(log_entry, expected_type, expected_team, expected_number):
    if not isinstance(log_entry, expected_type):
        raise ValueError(f"Expected {expected_type.__name__} but got {type(armour_entry)}")
    elif log_entry.team != expected_team or log_entry.player != expected_number:
        raise ValueError(f"Expected {expected_type.__name__} for "
                         f"{expected_team} #{expected_number}"
                         f" but got {log_entry.team} #{log_entry.player}")
