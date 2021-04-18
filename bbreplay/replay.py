# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import sqlite3
from collections import namedtuple
from . import other_team, CoinToss, TeamType, ActionResult, BlockResult, Skills, InjuryRollResult, \
    PITCH_LENGTH, PITCH_WIDTH, TOP_ENDZONE_IDX, BOTTOM_ENDZONE_IDX, OFF_PITCH_POSITION
from .command import *
from .log import parse_log_entries, MatchLogEntry, StupidEntry, DodgeEntry, SkillEntry, ArmourValueRollEntry, \
    PickupEntry, TentacledEntry, RerollEntry, TurnOverEntry, BlockLogEntry, BounceLogEntry, FoulAppearanceEntry
from .state import GameState, StartTurn, EndTurn
from .teams import Team


MatchEvent = namedtuple('Match', [])
CoinTossEvent = namedtuple('CoinToss', ['toss_team', 'toss_choice', 'toss_result', 'role_team', 'role_choice'])
TeamSetupComplete = namedtuple('TeamSetupComplete', ['team', 'player_positions'])
SetupComplete = namedtuple('SetupComplete', ['board'])
Kickoff = namedtuple('Kickoff', ['target', 'scatter_direction', 'scatter_distance', 'bounces', 'board'])
Movement = namedtuple('Movement', ['player', 'source_space', 'target_space', 'board'])
FailedMovement = namedtuple('FailedMovement', ['player', 'source_space', 'target_space'])
Block = namedtuple('Block', ['blocking_player', 'blocked_player', 'dice', 'result'])
Blitz = namedtuple('Blitz', ['blitzing_player', 'blitzed_player'])
DodgeBlock = namedtuple('DodgeBlock', ['blocking_player', 'blocked_player'])
BlockBothDown = namedtuple('BlockBothDown', ['player'])
Pushback = namedtuple('Pushback', ['pushing_player', 'pushed_player', 'source_space', 'taget_space', 'board'])
FollowUp = namedtuple('Followup', ['following_player', 'followed_player', 'source_space', 'target_space', 'board'])
ArmourRoll = namedtuple('ArmourRoll', ['player', 'result'])
InjuryRoll = namedtuple('InjuryRoll', ['player', 'result'])
Casualty = namedtuple('Casualty', ['player', 'injury'])
Dodge = namedtuple('Dodge', ['player', 'result'])
DivingTackle = namedtuple('DivingTackle', ['player', 'target_space'])
Pro = namedtuple('Pro', ['player', 'result'])
Pickup = namedtuple('Pickup', ['player', 'position', 'result'])
PlayerDown = namedtuple('PlayerDown', ['player'])
ConditionCheck = namedtuple('ConditionCheck', ['player', 'condition', 'result'])
Tentacle = namedtuple('Tentacle', ['dodging_player', 'tentacle_player', 'result'])
Reroll = namedtuple('Reroll', ['team', 'type'])
Bounce = namedtuple('Bounce', ['start_space', 'end_space', 'scatter_direction', 'board'])


class ReturnWrapper:
    # Ugly work-around class to let us pass back unused objects and still "yield from"
    def __init__(self):
        self.command = None
        self.log_entries = None


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

        log_entry = self.__log_entries[0][0]

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

    def __next_generator(self, log_entries):
        return self.__generator(next(log_entries))

    def events(self):
        log_entries = self.__generator(log_entry for log_entry in self.__log_entries)
        cmds = self.__generator(cmd for cmd in self.__commands if not cmd.is_verbose)

        match_log_entries = next(log_entries)
        yield MatchEvent()

        toss_cmd = find_next(cmds, CoinTossCommand)
        toss_log = match_log_entries[1]
        role_cmd = find_next(cmds, RoleCommand)
        role_log = next(log_entries)[0]
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

        board = GameState(self.home_team, self.away_team)
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
        kickoff_direction, kickoff_scatter = next(log_entries)
        # TODO: Handle no bounce when it gets caught straight away
        kickoff_bounce = next(log_entries)[0]
        # TODO: Handle second bounce for "Changing Weather" event rolling "Nice" again
        ball_dest = kickoff_cmd.position.scatter(kickoff_direction.direction, kickoff_scatter.distance)\
                                        .scatter(kickoff_bounce.direction)
        board.set_ball_position(ball_dest)
        yield Kickoff(kickoff_cmd.position, kickoff_direction.direction, kickoff_scatter.distance,
                      [kickoff_bounce.direction], board)

        yield board.start_match(role_cmd.team, role_cmd.choice)

        prev_cmd = None

        while True:
            prev_cmd = cmd
            cmd = next(cmds, None)
            if cmd is None:
                break
            cmd_type = type(cmd)
            if isinstance(cmd, TargetPlayerCommand):
                target = cmd
                targeting_player = self.get_team(target.team).get_player(target.player_idx)
                target_by_idx = self.get_team(target.target_team).get_player(target.target_player)
                target_log_entries = None
                if Skills.REALLY_STUPID in targeting_player.skills:
                    target_log_entries = self.__next_generator(log_entries)
                    log_entry = next(target_log_entries)
                    validate_log_entry(log_entry, StupidEntry, target.team, targeting_player.number)
                    yield ConditionCheck(targeting_player, 'Really Stupid', log_entry.result)
                    if log_entry.result != ActionResult.SUCCESS:
                        # The stupid stopped us
                        continue
                if Skills.FOUL_APPEARANCE in target_by_idx.skills:
                    if not target_log_entries:
                        target_log_entries = self.__next_generator(log_entries)
                    log_entry = next(target_log_entries)
                    validate_log_entry(log_entry, FoulAppearanceEntry, target.team, targeting_player.number)
                    yield ConditionCheck(targeting_player, 'Foul Appearance', log_entry.result)

                cmd = next(cmds)
                if isinstance(cmd, MovementCommand):
                    yield Blitz(targeting_player, target_by_idx)
                    unused = ReturnWrapper()
                    yield from self.__process_movement(targeting_player, cmd, cmds,
                                                       target_log_entries, log_entries, board, unused)
                    cmd = unused.command
                    target_log_entries = unused.log_entries
                elif board.is_prone(targeting_player):
                    board.unset_prone(targeting_player)
                    yield Blitz(targeting_player, target_by_idx)
                if not target_log_entries:
                    target_log_entries = self.__next_generator(log_entries)
                if isinstance(cmd, BlockCommand):
                    block = cmd
                    blocking_player = targeting_player
                    block_dice = next(target_log_entries)
                    block_choice = next(cmds)
                    if isinstance(block_choice, ProRerollCommand):
                        reroll = next(target_log_entries)
                        yield Pro(blocking_player, reroll.result)
                        if reroll.result == ActionResult.SUCCESS:
                            yield Reroll(reroll.team, 'Pro')
                            _ = next(target_log_entries)  # Burn the random duplication
                        else:
                            _ = next(cmds)  # Burn the reroll prompt that shows as a block dice choice
                        block_dice = next(target_log_entries)
                        block_choice = next(cmds)
                    elif isinstance(block_choice, RerollCommand):
                        reroll = next(target_log_entries)
                        yield Reroll(reroll.team, 'Team Reroll')
                        block_dice = next(target_log_entries)
                        block_choice = next(cmds)
                    target_by_coords = board.get_position(block.position)
                    if target_by_coords != target_by_idx:
                        raise ValueError(f"{target} targetted {target_by_idx} but {block} targetted {target_by_coords}")
                    chosen_block_dice = block_dice.results[block_choice.dice_idx]
                    yield Block(blocking_player, target_by_idx,
                                block_dice.results, chosen_block_dice)

                    if chosen_block_dice == BlockResult.PUSHED or chosen_block_dice == BlockResult.DEFENDER_DOWN \
                        or chosen_block_dice == BlockResult.DEFENDER_STUMBLES:
                        block_result = next(cmds)
                        old_coords = target_by_idx.position
                        origin_coords = blocking_player.position
                        board.reset_position(old_coords)
                        pushing_player = blocking_player
                        pushed_player = target_by_coords
                        while True:
                            if isinstance(block_result, PushbackCommand):
                                new_coords = block_result.position
                                dest_content = board.get_position(new_coords)
                                origin_coords = pushed_player.position
                                board.set_position(new_coords, pushed_player)
                                yield Pushback(pushing_player, pushed_player, old_coords, new_coords, board)
                                block_result = next(cmds)
                                if not dest_content:
                                    break
                                pushing_player = pushed_player
                                pushed_player = dest_content
                                old_coords = new_coords
                            elif isinstance(block_result, FollowUpChoiceCommand):
                                # FollowUp without Pushback means they only had one space to go to
                                new_coords = calculate_pushback(origin_coords, old_coords, board)
                                board.set_position(new_coords, pushed_player)
                                yield Pushback(pushing_player, pushed_player, old_coords, new_coords, board)
                                break
                            else:
                                raise ValueError("Expected PushbackCommand after "
                                                 f"{chosen_block_dice} but got {type(block_result).__name__}")

                        # Follow-up
                        if block_result.choice:
                            old_coords = blocking_player.position
                            board.reset_position(old_coords)
                            board.set_position(block.position, blocking_player)
                            yield FollowUp(blocking_player, target_by_idx, old_coords, block.position, board)

                    attacker_avoided = False
                    defender_avoided = False

                    if chosen_block_dice == BlockResult.DEFENDER_STUMBLES and Skills.DODGE in target_by_idx.skills:
                        skill_entry = next(target_log_entries)
                        validate_skill_log_entry(skill_entry, target_by_idx, Skills.DODGE)
                        yield DodgeBlock(blocking_player, target_by_idx)
                        defender_avoided = True
                    elif chosen_block_dice == BlockResult.BOTH_DOWN:
                        if Skills.BLOCK in blocking_player.skills:
                            skill_entry = next(target_log_entries)
                            validate_skill_log_entry(skill_entry, blocking_player, Skills.BLOCK)
                            yield BlockBothDown(blocking_player)
                            attacker_avoided = True
                        if Skills.BLOCK in target_by_idx.skills:
                            skill_entry = next(target_log_entries)
                            validate_skill_log_entry(skill_entry, target_by_idx, Skills.BLOCK)
                            yield BlockBothDown(target_by_idx)
                            defender_avoided = True


                    if (chosen_block_dice == BlockResult.ATTACKER_DOWN \
                        or chosen_block_dice == BlockResult.BOTH_DOWN) \
                            and not attacker_avoided:
                        armour_entry = next(target_log_entries)
                        yield from self.__handle_armour_roll(armour_entry, target_log_entries, blocking_player, board)
                    if (chosen_block_dice == BlockResult.DEFENDER_DOWN \
                        or chosen_block_dice == BlockResult.DEFENDER_STUMBLES \
                        or chosen_block_dice == BlockResult.BOTH_DOWN) \
                        and not defender_avoided:
                        armour_entry = next(target_log_entries)
                        yield from self.__handle_armour_roll(armour_entry, target_log_entries, target_by_idx, board)
                    log_entry = next(target_log_entries, None)
                    if isinstance(log_entry, TurnOverEntry):
                        validate_log_entry(log_entry, TurnOverEntry, blocking_player.team.team_type)
                        yield from board.end_turn(log_entry.team, log_entry.reason)
                    elif isinstance(log_entry, BounceLogEntry):
                        ball_position = target_by_coords.position.scatter(log_entry.direction)
                        board.set_ball_position(ball_position)
                        yield Bounce(block.position, ball_position, log_entry.direction, board)
            elif isinstance(cmd, MovementCommand):
                player = self.get_team(cmd.team).get_player(cmd.player_idx)
                # We stop when the movement stops, so the returned command is the EndMovementCommand
                yield from self.__process_movement(player, cmd, cmds, None, log_entries, board)
            elif cmd_type is Command or cmd_type is PreKickoffCompleteCommand or cmd_type is DeclineRerollCommand:
                continue
            elif cmd_type is BlockDiceChoiceCommand and type(prev_cmd) is MovementCommand:
                print("Skipping an unexpected BlockDiceChoiceCommand - possibly related to rerolls")
            elif cmd_type is EndTurnCommand:
                yield from board.end_turn(cmd.team, 'End Turn')
            else:
                print(f"No handling for {cmd}")
                break

    def get_commands(self):
        return self.__commands

    def get_log_entries(self):
        return self.__log_entries

    def __handle_armour_roll(self, roll_entry, log_entries, player, board):
        validate_log_entry(roll_entry, ArmourValueRollEntry,
                           player.team.team_type, player.number)
        board.set_prone(player)
        yield PlayerDown(player)
        yield ArmourRoll(player, roll_entry.result)
        if roll_entry.result == ActionResult.SUCCESS:
            injury_roll = next(log_entries)
            yield InjuryRoll(player, injury_roll.result)
            if injury_roll.result == InjuryRollResult.KO:
                # Remove the player from the pitch
                board.reset_position(player.position)
            elif injury_roll.result == InjuryRollResult.INJURED:
                # Remove the player from the pitch
                board.reset_position(player.position)
                casualty_roll = next(log_entries)
                yield Casualty(player, casualty_roll.injury)


    def __process_movement(self, player, cmd, cmds, cur_log_entries, log_entries, board, unused=None):
        failed_movement = False
        pickup_entry = None
        diving_tackle_entry = None
        start_space = player.position
        move_log_entries = None
        turnover = None
        move_log_entries = cur_log_entries
        moves = []
        is_prone = board.is_prone(player)

        # We can't just use "while true" and check for EndMovementCommand because a blitz is
        # movement followed by a Block without an EndMovementCommand
        while isinstance(cmd, MovementCommand):
            moves.append(cmd)
            if isinstance(cmd, EndMovementCommand):
                break
            cmd = next(cmds)

        if not isinstance(cmd, MovementCommand) and unused:
            unused.command = cmd

        if Skills.REALLY_STUPID in player.skills:
            if not move_log_entries:
                move_log_entries = self.__next_generator(log_entries)
            log_entry = next(move_log_entries)
            validate_log_entry(log_entry, StupidEntry, cmd.team, player.number)
            yield ConditionCheck(player, 'Really Stupid', log_entry.result)
            if log_entry.result != ActionResult.SUCCESS:
                failed_movement = True
                log_entry = next(move_log_entries, None)
                if log_entry:
                    validate_log_entry(log_entry, RerollEntry, player.team.team_type)
                    cmd = next(cmds)
                    if isinstance(cmd, ProRerollCommand):
                        if log_entry.result == ActionResult.SUCCESS:
                            yield Reroll(log_entry.team, 'Pro')
                            log_entry = next(move_log_entries)
                            yield ConditionCheck(player, 'Really Stupid', log_entry.result)
                            if log_entry.result == ActionResult.SUCCESS:
                                failed_movement = False
                    elif isinstance(cmd, RerollEntry):
                        yield Reroll(cmd.team, 'Team Reroll')
                    else:
                        raise ValueError("No RerollCommand to go with RerollEntry")

        for movement in moves:
            target_space = movement.position
            if not failed_movement and is_dodge(board, player, target_space):
                if not move_log_entries:
                    move_log_entries = self.__next_generator(log_entries)
                while True:
                    log_entry = next(move_log_entries, None)
                    if not log_entry:
                        break
                    elif isinstance(log_entry, PickupEntry):
                        validate_log_entry(log_entry, PickupEntry, player.team.team_type, player.number)
                        pickup_entry = log_entry
                    elif isinstance(log_entry, DodgeEntry):
                        validate_log_entry(log_entry, DodgeEntry, player.team.team_type, player.number)
                        yield Dodge(player, log_entry.result)
                    elif isinstance(log_entry, TentacledEntry):
                        validate_log_entry(log_entry, TentacledEntry, player.team.team_type, player.number)
                        attacker = self.get_team(log_entry.attacking_team)\
                                       .get_player_by_number(log_entry.attacking_player)
                        yield Tentacle(player, attacker, log_entry.result)
                    elif isinstance(log_entry, TurnOverEntry):
                        validate_log_entry(log_entry, TurnOverEntry, player.team.team_type)
                        turnover = log_entry.reason
                    elif isinstance(log_entry, SkillEntry) and log_entry.skill == Skills.DIVING_TACKLE:
                        diving_tackle_entry = log_entry
                        continue
                    else:
                        raise ValueError("Looking for dodge-related log entries but got "
                                         f"{type(log_entry).__name__}")

                    if isinstance(log_entry, DodgeEntry) and log_entry.result == ActionResult.SUCCESS:
                        failed_movement = False
                        break
                    elif isinstance(log_entry, TurnOverEntry):
                        break
                    elif log_entry.result != ActionResult.SUCCESS:
                        failed_movement = True
                        log_entry = next(move_log_entries, None)
                        if isinstance(log_entry, RerollEntry):
                            validate_log_entry(log_entry, RerollEntry, player.team.team_type)
                            cmd = next(cmds)
                            if not isinstance(cmd, RerollCommand):
                                raise ValueError("No RerollCommand to go with RerollEntry")
                            else:
                                yield Reroll(cmd.team, 'Team Reroll')
                        elif isinstance(log_entry, ArmourValueRollEntry):
                            yield from self.__handle_armour_roll(log_entry, move_log_entries, player, board)
                        else:
                            cmd = next(cmds)
                            if not isinstance(cmd, DeclineRerollCommand):
                                raise ValueError("No DeclineRerollCommand to go with failed movement action")
                            cmd = next(cmds)
                            if not isinstance(cmd, BlockDiceChoiceCommand):
                                raise ValueError("No BlockDiceChoiceCommand? to go with DeclineRerollCommand")
                            break

            if target_space == board.get_ball_position() and not pickup_entry:
                if not move_log_entries:
                    move_log_entries = self.__next_generator(log_entries)
                log_entry = next(move_log_entries)
                validate_log_entry(log_entry, PickupEntry, player.team.team_type, player.number)
                pickup_entry = log_entry
            else:
                target_contents = board.get_position(target_space)
                if target_contents and target_contents != player:
                    raise ValueError(f"{player} tried to move to occupied space {target_space}")

            if not failed_movement:
                if is_prone:
                    board.unset_prone(player)
                    is_prone = False
                board.reset_position(start_space)
                board.set_position(target_space, player)
                yield Movement(player, start_space, target_space, board)
            elif isinstance(log_entry, TurnOverEntry):
                board.reset_position(start_space)
                board.set_position(target_space, player)
                yield FailedMovement(player, start_space, target_space)
            else:
                # Failure due to Tentacles etc
                if is_prone:
                    board.unset_prone(player)
                    is_prone = False
                yield FailedMovement(player, start_space, target_space)

            if diving_tackle_entry:
                team = self.get_team(diving_tackle_entry.team)
                diving_player = team.get_player_by_number(diving_tackle_entry.player)
                board.reset_position(diving_player.position)
                board.set_position(start_space, diving_player)
                board.set_prone(diving_player)
                yield DivingTackle(diving_player, start_space)

            if pickup_entry:
                yield Pickup(player, movement.position, pickup_entry.result)
                if pickup_entry.result != ActionResult.SUCCESS:
                    failed_movement = True
                else:
                    board.set_ball_carrier(player)
                pickup_entry = None

            start_space = target_space

        if turnover:
            yield from board.end_turn(player.team.team_type, turnover)

        if unused:
            unused.log_entries = move_log_entries


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


def validate_log_entry(log_entry, expected_type, expected_team, expected_number=None):
    if not isinstance(log_entry, expected_type):
        raise ValueError(f"Expected {expected_type.__name__} but got {type(log_entry)}")
    elif log_entry.team != expected_team or (expected_number is not None and log_entry.player != expected_number):
        if expected_number is not None:
            raise ValueError(f"Expected {expected_type.__name__} for "
                             f"{expected_team} #{expected_number}"
                             f" but got {log_entry.team} #{log_entry.player}")
        else:
            raise ValueError(f"Expected {expected_type.__name__} for "
                             f"{expected_team} but got {log_entry.team}")


def validate_skill_log_entry(log_entry, player, skill):
    validate_log_entry(log_entry, SkillEntry, player.team.team_type, player.number)
    if skill not in player.skills:
        raise ValueError(f"Got skill entry for {skill} but player has {player.skills}")


def calculate_pushback(blocker_coords, old_coords, board):
    # Note: We invert the calculation so that we can avoid multiplying by -1 later
    x_diff = old_coords.x - blocker_coords.x
    y_diff = old_coords.y - blocker_coords.y
    if x_diff != 0:
        if y_diff != 0:
            possible_coords = [old_coords.add(x_diff, y_diff), old_coords.add(x_diff, 0), old_coords.add(0, y_diff)]
        else:
            possible_coords = [old_coords.add(x_diff, -1), old_coords.add(x_diff, 0), old_coords.add(x_diff, 1)]
    else:
        possible_coords = [old_coords.add(-1, y_diff), old_coords.add(0, y_diff), old_coords.add(1, y_diff)]

    for possible_coord in possible_coords:
        if not board.get_position(possible_coord):
            return possible_coord
