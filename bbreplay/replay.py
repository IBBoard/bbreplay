# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import sqlite3
from collections import namedtuple
from . import other_team, CoinToss, TeamType, ActionResult, BlockResult, Skills, InjuryRollResult, \
    KickoffEvent, Role, ThrowResult, \
    PITCH_LENGTH, PITCH_WIDTH, LAST_COLUMN_IDX, NEAR_ENDZONE_IDX, FAR_ENDZONE_IDX, OFF_PITCH_POSITION
from .command import *
from .log import parse_log_entries, MatchLogEntry, StupidEntry, DodgeEntry, SkillEntry, ArmourValueRollEntry, \
    PickupEntry, TentacledEntry, RerollEntry, TurnOverEntry, BounceLogEntry, FoulAppearanceEntry, \
    ThrowInDirectionLogEntry, CatchEntry, KORecoveryEntry, ThrowEntry
from .state import GameState
from .state import StartTurn, EndTurn, WeatherTuple, AbandonMatch  # noqa: F401 - these are for export
from .teams import Team


MatchEvent = namedtuple('Match', [])
CoinTossEvent = namedtuple('CoinToss', ['toss_team', 'toss_choice', 'toss_result', 'role_team', 'role_choice'])
TeamSetupComplete = namedtuple('TeamSetupComplete', ['team', 'player_positions'])
SetupComplete = namedtuple('SetupComplete', ['board'])
Kickoff = namedtuple('Kickoff', ['target', 'scatter_direction', 'scatter_distance', 'board'])
KickoffEventTuple = namedtuple('KickoffEvent', ['result'])
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
Casualty = namedtuple('Casualty', ['player', 'result'])
Apothecary = namedtuple('Apothecary', ['player', 'new_injury', 'casualty'])
Dodge = namedtuple('Dodge', ['player', 'result'])
DivingTackle = namedtuple('DivingTackle', ['player', 'target_space'])
Pro = namedtuple('Pro', ['player', 'result'])
Pickup = namedtuple('Pickup', ['player', 'position', 'result'])
Pass = namedtuple('Pass', ['player', 'target', 'result', 'board'])
Catch = namedtuple('Catch', ['player', 'result', 'board'])
PlayerDown = namedtuple('PlayerDown', ['player'])
ConditionCheck = namedtuple('ConditionCheck', ['player', 'condition', 'result'])
Tentacle = namedtuple('Tentacle', ['dodging_player', 'tentacle_player', 'result'])
Reroll = namedtuple('Reroll', ['team', 'type'])
Bounce = namedtuple('Bounce', ['start_space', 'end_space', 'scatter_direction', 'board'])
ThrowIn = namedtuple('ThrowIn', ['start_space', 'end_space', 'direction', 'distance', 'board'])
Touchdown = namedtuple('Touchdown', ['player', 'board'])

END_REASON_TOUCHDOWN = 'Touchdown!'
END_REASON_ABANDON = 'Abandon Match'


class ReturnWrapper:
    # Ugly work-around class to let us pass back unused objects and still "yield from"
    def __init__(self):
        self.command = None
        self.log_entries = None


class Replay:
    def __init__(self, db_path, log_path):
        self.__db = sqlite3.connect(db_path)
        cur = self.__db.cursor()
        cur.execute('SELECT team.strName, race.DATA_CONSTANT, iValue, iPopularity, iRerolls '
                    'FROM Home_Team_Listing team INNER JOIN Home_Races race ON idRaces = race.ID')
        self.home_team = Team(*cur.fetchone(), TeamType.HOME, self.__db)
        cur.execute('SELECT team.strName, race.DATA_CONSTANT, iValue, iPopularity, iRerolls '
                    'FROM Away_Team_Listing team INNER JOIN Away_Races race ON idRaces = race.ID')
        self.away_team = Team(*cur.fetchone(), TeamType.AWAY, self.__db)
        self.__commands = [create_command(self, row)
                           for row in cur.execute('SELECT * FROM Replay_NetCommands ORDER BY ID')]
        cur.close()
        self.__log_entries = parse_log_entries(log_path)

        log_entry = self.__log_entries[1][0]

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

        randomisation = next(log_entries)[0]
        match_log_entries = next(log_entries)
        yield MatchEvent()

        toss_cmd = find_next(cmds, CoinTossCommand)
        toss_log = match_log_entries[1]
        role_cmd = find_next(cmds, RoleCommand)
        role_log = next(log_entries)[0]
        toss_team = toss_cmd.team if toss_cmd.team != TeamType.HOTSEAT else randomisation.team
        if toss_team != toss_log.team or toss_cmd.choice != toss_log.choice:
            raise ValueError("Mismatch in toss details")
        if role_cmd.team == TeamType.HOTSEAT:
            role_team = randomisation.team if toss_log.choice == randomisation.result \
                else other_team(randomisation.result)
        else:
            role_team = role_cmd.team
        if role_team != role_log.team or role_cmd.choice != role_log.choice:
            raise ValueError("Mismatch in role details")
        toss_choice = toss_cmd.choice
        if toss_team == role_team:
            toss_result = toss_choice
        elif toss_choice == CoinToss.HEADS:
            toss_result = CoinToss.TAILS
        else:
            toss_result = CoinToss.HEADS
        yield CoinTossEvent(toss_team, toss_choice, toss_result, role_team, role_cmd.choice)
        receiver = role_team if role_cmd.choice == Role.RECEIVE else other_team(role_team)
        board = GameState(self.home_team, self.away_team, receiver)
        weather = next(log_entries)[0]
        yield board.set_weather(weather.result)

        cmd = find_next(cmds, SetupCommand)
        yield from self.__process_kickoff(cmd, cmds, log_entries, board, True)

        while True:
            drive_ended = False
            while not drive_ended:
                for event in self.__process_turn(cmds, log_entries, board):
                    event_type = type(event)
                    if event_type in [Touchdown]:
                        drive_ended = True
                    elif event_type is AbandonMatch:
                        return
                    yield event
                    if event_type is EndTurn and board.turn == 8 and board.turn_team.team_type != receiver:
                        yield board.halftime()
            yield from self.__process_kickoff(next(cmds), cmds, log_entries, board, False)

    def get_commands(self):
        return self.__commands

    def get_log_entries(self):
        return self.__log_entries

    def __process_kickoff(self, cmd, cmds, log_entries, board, is_match_start):
        deployments_finished = 0
        team = None

        board.prepare_setup()

        kickoff_log_events = next(log_entries)

        if type(kickoff_log_events[0]) is KORecoveryEntry:
            for event in kickoff_log_events:
                if event.result == ActionResult.SUCCESS:
                    player = self.get_team(event.team).get_player_by_number(event.player)
                    board.unset_injured(player)
            kickoff_log_events = next(log_entries)
        # Else leave it for the kickoff event

        while True:
            cmd_type = type(cmd)
            if cmd_type is SetupCompleteCommand:
                deployments_finished += 1
                for i in range(PITCH_WIDTH):
                    endzone_contents = board[NEAR_ENDZONE_IDX][i]
                    if endzone_contents:
                        board[NEAR_ENDZONE_IDX][i] = None
                        endzone_contents.position = OFF_PITCH_POSITION
                    endzone_contents = board[FAR_ENDZONE_IDX][i]
                    if endzone_contents:
                        board[FAR_ENDZONE_IDX][i] = None
                        endzone_contents.position = OFF_PITCH_POSITION
                yield TeamSetupComplete(team.team_type, team.get_players())
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

            if space_contents and space_contents != player:
                if old_coords:
                    board.set_position(old_coords, space_contents)
                else:
                    space_contents.position = OFF_PITCH_POSITION

            board.set_position(coords, player)
            cmd = next(cmds)

        kickoff_cmd = find_next(cmds, KickoffCommand)
        kickoff_direction, kickoff_scatter = kickoff_log_events
        ball_dest = kickoff_cmd.position.scatter(kickoff_direction.direction, kickoff_scatter.distance)
        board.set_ball_position(ball_dest)
        yield Kickoff(kickoff_cmd.position, kickoff_direction.direction, kickoff_scatter.distance, board)

        kickoff_event = next(log_entries)[0]
        yield KickoffEventTuple(kickoff_event.result)
        ball_bounces = True
        if kickoff_event.result == KickoffEvent.BLITZ:
            board.blitz()
            yield from self.__process_turn(cmds, log_entries, board)
        elif kickoff_event.result == KickoffEvent.CHANGING_WEATHER:
            weather = next(log_entries)[0]  # Sometimes this duplicates, but we don't care
            yield board.set_weather(weather.result)
        elif kickoff_event.result == KickoffEvent.HIGH_KICK:
            high_kick_log = next(log_entries)
            high_kick_catch = high_kick_log[0]
            catcher = self.get_team(high_kick_catch.team).get_player_by_number(high_kick_catch.player)
            old_position = catcher.position
            new_position = board.get_ball_position()
            board.reset_position(old_position)
            board.set_position(new_position, catcher)
            if high_kick_catch.result == ActionResult.SUCCESS:
                board.set_ball_carrier(catcher)
                ball_bounces = False
            yield Movement(catcher, old_position, new_position, board)
            yield Catch(catcher, high_kick_catch.result, board)

        yield from board.kickoff()

        if ball_bounces:
            # TODO: Handle no bounce when it gets caught straight away
            kickoff_bounce = next(log_entries)[0]
            # TODO: Handle second bounce for "Changing Weather" event rolling "Nice" again
            ball_dest = ball_dest.scatter(kickoff_bounce.direction)
            board.set_ball_position(ball_dest)

    def __process_turn(self, cmds, log_entries, board):
        cmd = None
        end_reason = None

        while not end_reason:
            cmd = next(cmds, None)
            if cmd is None:
                break
            cmd_type = type(cmd)
            if isinstance(cmd, TargetPlayerCommand):
                target = cmd
                targeting_player = self.get_team(target.team).get_player(target.player_idx)
                target_by_idx = self.get_team(target.target_team).get_player(target.target_player)
                target_log_entries = None
                is_block = targeting_player.team != target_by_idx.team
                if is_block and Skills.FOUL_APPEARANCE in target_by_idx.skills:
                    if not target_log_entries:
                        target_log_entries = self.__next_generator(log_entries)
                    log_entry = next(target_log_entries)
                    validate_log_entry(log_entry, FoulAppearanceEntry, target.team, targeting_player.number)
                    yield ConditionCheck(targeting_player, 'Foul Appearance', log_entry.result)

                cmd = next(cmds)
                if isinstance(cmd, MovementCommand):
                    if is_block:
                        yield Blitz(targeting_player, target_by_idx)
                    unused = ReturnWrapper()
                    yield from self.__process_movement(targeting_player, cmd, cmds,
                                                       target_log_entries, log_entries, board, unused)
                    cmd = unused.command
                    target_log_entries = unused.log_entries
                else:
                    unused = ReturnWrapper()
                    yield from self.__process_stupidity(targeting_player, cmd, cmds, target_log_entries, log_entries,
                                                        board, unused)
                    target_log_entries = unused.log_entries
                    if board.is_prone(targeting_player):
                        board.unset_prone(targeting_player)
                        if is_block:
                            yield Blitz(targeting_player, target_by_idx)
                if not target_log_entries:
                    target_log_entries = self.__next_generator(log_entries)
                if isinstance(cmd, TargetSpaceCommand) and is_block:
                    if Skills.DUMP_OFF in target_by_idx.skills and board.get_ball_carrier() == target_by_idx:
                        dumpoff_cmd = next(cmds)
                        if dumpoff_cmd.team != target_by_idx.team.team_type:
                            raise ValueError(f"{target_by_idx} used dump off but command was for {dumpoff_cmd.team}")
                        throw_cmd = next(cmds)
                        yield from self.__process_pass(target_by_idx, throw_cmd, cmds, target_log_entries, board)
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
                        elif len(block_dice.results) == 2 and block_dice.results[0] == block_dice.results[1]:
                            _ = next(cmds)  # Burn the reroll prompt that shows as a block dice choice
                        block_dice = next(target_log_entries)
                        block_choice = next(cmds)
                    elif isinstance(block_choice, RerollCommand):
                        board.use_reroll(blocking_player.team.team_type)
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
                        origin_coords = blocking_player.position
                        old_coords = target_by_coords.position
                        pushbacks = calculate_pushbacks(origin_coords, old_coords, board)
                        if len(pushbacks) != 1 or Skills.FRENZY not in blocking_player.skills:
                            cmd = next(cmds)
                            board.reset_position(old_coords)
                            pushing_player = blocking_player
                            pushed_player = target_by_coords
                            while True:
                                if isinstance(cmd, PushbackCommand):
                                    new_coords = cmd.position
                                    dest_content = board.get_position(new_coords)
                                    origin_coords = pushed_player.position
                                    board.set_position(new_coords, pushed_player)
                                    yield Pushback(pushing_player, pushed_player, old_coords, new_coords, board)
                                    cmd = next(cmds)
                                    if not dest_content:
                                        break
                                    pushing_player = pushed_player
                                    pushed_player = dest_content
                                    old_coords = new_coords
                                elif isinstance(cmd, FollowUpChoiceCommand):
                                    # FollowUp without Pushback means they only had one space to go to
                                    new_coords = calculate_pushback(origin_coords, old_coords, board)
                                    board.set_position(new_coords, pushed_player)
                                    yield Pushback(pushing_player, pushed_player, old_coords, new_coords, board)
                                    break
                                elif isinstance(cmd, MovementCommand):
                                    yield from self.__process_movement(pushing_player, cmd, cmds,
                                                                       target_log_entries, log_entries, board)
                                    break
                                else:
                                    raise ValueError("Expected PushbackCommand after "
                                                     f"{chosen_block_dice} but got {type(cmd).__name__}")
                        else:
                            # Frenzy with one destination won't have a Pushback (one dest) or a
                            # FollowUp (because Frenzy always does) so it needs special handling
                            board.set_position(pushbacks[0], target_by_coords)
                            board.reset_position(old_coords)

                        # Follow-up
                        if Skills.FRENZY in blocking_player.skills or \
                           (isinstance(cmd, FollowUpChoiceCommand) and cmd.choice):
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

                    attacker_injured = False
                    attacker_casualty = False
                    if (chosen_block_dice == BlockResult.ATTACKER_DOWN
                        or chosen_block_dice == BlockResult.BOTH_DOWN) \
                            and not attacker_avoided:
                        armour_entry = next(target_log_entries)
                        for event in self.__handle_armour_roll(armour_entry, target_log_entries,
                                                               blocking_player, board):
                            yield event
                            if isinstance(event, InjuryRoll):
                                attacker_injured = event.result != InjuryRollResult.STUNNED
                                attacker_casualty = event.result == InjuryRollResult.INJURED
                                if attacker_injured and not attacker_casualty:
                                    yield from self.__process_apothecary(blocking_player, event.result,
                                                                         CasualtyResult.NONE,
                                                                         cmds, target_log_entries, board)

                    defender_injured = False
                    defender_casualty = False
                    if (chosen_block_dice == BlockResult.DEFENDER_DOWN
                       or chosen_block_dice == BlockResult.DEFENDER_STUMBLES
                       or chosen_block_dice == BlockResult.BOTH_DOWN) \
                       and not defender_avoided:
                        armour_entry = next(target_log_entries)
                        pushed_into_ball = target_by_idx.position == board.get_ball_position()
                        for event in self.__handle_armour_roll(armour_entry, target_log_entries, target_by_idx, board):
                            yield event
                            if isinstance(event, InjuryRoll):
                                defender_injured = event.result != InjuryRollResult.STUNNED
                                defender_casualty = event.result == InjuryRollResult.INJURED
                                if defender_injured and not defender_casualty:
                                    yield from self.__process_apothecary(target_by_idx, event.result,
                                                                         CasualtyResult.NONE,
                                                                         cmds, target_log_entries, board)
                        if board.get_ball_carrier() == target_by_idx or pushed_into_ball:
                            yield from self.__process_ball_movement(target_log_entries, blocking_player, board)

                    if isinstance(cmd, MovementCommand):
                        yield from self.__process_movement(blocking_player, cmd, cmds,
                                                           target_log_entries, log_entries, board)
                    if attacker_casualty:
                        yield from self.__process_casualty(blocking_player, cmds, target_log_entries, board)

                    if defender_casualty:
                        yield from self.__process_casualty(target_by_idx, cmds, target_log_entries, board)
                    log_entry = next(target_log_entries, None)
                    while log_entry:
                        log_entry_type = type(log_entry)
                        if log_entry_type is TurnOverEntry:
                            validate_log_entry(log_entry, TurnOverEntry, blocking_player.team.team_type)
                            yield from board.change_turn(blocking_player.team.team_type, log_entry.reason)
                        else:
                            raise NotImplementedError(f"Unhandled log entry - {log_entry}")
                        log_entry = next(target_log_entries, None)
                elif isinstance(cmd, TargetSpaceCommand) and not is_block:
                    pass_cmd = cmd
                    player_pos = targeting_player.position
                    if abs(pass_cmd.x - player_pos.x) > 1 or pass_cmd.y - player_pos.y > 1:
                        # Pass (Launch)
                        raise NotImplementedError("Not handling passes yet")
                    # Else hand-off - doesn't have the pass part, just the catch
                    catch_entry = next(target_log_entries)
                    target_by_coords = board.get_position(pass_cmd.position)
                    validate_log_entry(catch_entry, CatchEntry, pass_cmd.team, target_by_coords.number)
                    if catch_entry.result == ActionResult.SUCCESS:
                        board.set_ball_carrier(target_by_idx)
                else:
                    raise ValueError(f"Unexpected post-target command {cmd}")
            elif isinstance(cmd, MovementCommand):
                player = self.get_team(cmd.team).get_player(cmd.player_idx)
                # We stop when the movement stops, so the returned command is the EndMovementCommand
                yield from self.__process_movement(player, cmd, cmds, None, log_entries, board)
                if board.get_ball_carrier() == player and \
                   (player.position.y == NEAR_ENDZONE_IDX or player.position.y == FAR_ENDZONE_IDX):
                    board.score[player.team.team_type.value] += 1
                    yield Touchdown(player, board)
                    end_reason = END_REASON_TOUCHDOWN
            elif cmd_type is Command or cmd_type is PreKickoffCompleteCommand or cmd_type is DeclineRerollCommand:
                continue
            elif cmd_type is EndTurnCommand:
                end_reason = 'End Turn'
            elif cmd_type is AbandonMatchCommand:
                end_reason = END_REASON_ABANDON
            else:
                raise NotImplementedError(f"No handling for {cmd}")
                break

        if end_reason == END_REASON_ABANDON:
            yield from board.abandon_match(cmd.team)
        else:
            yield from board.end_turn(cmd.team, end_reason)
            if end_reason != END_REASON_TOUCHDOWN:
                # Touchdowns will be restarted by the setup and kickoff process
                yield from board.start_turn(other_team(cmd.team))

    def __handle_armour_roll(self, roll_entry, log_entries, player, board):
        validate_log_entry(roll_entry, ArmourValueRollEntry,
                           player.team.team_type, player.number)
        board.set_prone(player)
        yield PlayerDown(player)
        yield ArmourRoll(player, roll_entry.result)
        if roll_entry.result == ActionResult.SUCCESS:
            injury_roll = next(log_entries)
            yield InjuryRoll(player, injury_roll.result)
            if injury_roll.result != InjuryRollResult.STUNNED:
                board.reset_position(player.position)
                board.set_injured(player)

    def __process_casualty(self, player, cmds, log_entries, board):
        casualty_roll = next(log_entries)
        yield Casualty(player, casualty_roll.result)
        yield from self.__process_apothecary(player, InjuryRollResult.INJURED, casualty_roll.result,
                                             cmds, log_entries, board)

    def __process_apothecary(self, player, injury, casualty_result, cmds, log_entries, board):
        cmd = next(cmds)
        if not isinstance(cmd, ApothecaryCommand):
            raise ValueError(f"Expected ApothecaryCommand after injury but got {type(cmd).__name__}")
        if cmd.team != player.team.team_type or player.team.get_player_number(cmd.player) != player.number:
            raise ValueError(f"Expected ApothecaryCommand for {player.team.team_type} #{player.number} "
                             f"but got {cmd.team} #{player.team.get_player_number(cmd.player)}")
        if not cmd.used:
            # Let them suffer their fate!
            return
        if casualty_result == CasualtyResult.NONE:
            raise NotImplementedError("Not seen apothecary on KO")
        new_casualty_roll = next(log_entries)
        yield Apothecary(player, injury, new_casualty_roll.result)
        cmd = next(cmds)
        if not isinstance(cmd, ApothecaryChoiceCommand):
            raise ValueError(f"Expected ApothecaryChoiceCommand after injury but got {type(cmd).__name__}")
        if cmd.team != player.team.team_type or player.team.get_player_number(cmd.player) != player.number:
            raise ValueError(f"Expected ApothecaryChoiceCommand for {player.team.team_type} #{player.number} "
                             f"but got {cmd.team} #{player.team.get_player_number(cmd.player)}")
        if cmd.result != injury and cmd.result != new_casualty_roll.result:
            raise ValueError(f"Expected ApothecaryChoiceCommand result of {injury} or "
                             f"{new_casualty_roll.result} but got {cmd.result}")
        yield Casualty(player, cmd.result)

    def __process_stupidity(self, player, cmd, cmds, cur_log_entries, log_entries, board, unused=None):
        if Skills.REALLY_STUPID in player.skills and not board.tested_stupid(player):
            if not cur_log_entries:
                cur_log_entries = self.__next_generator(log_entries)
            log_entry = next(cur_log_entries)
            validate_log_entry(log_entry, StupidEntry, cmd.team, player.number)
            board.stupidity_test(player, log_entry.result)
            yield ConditionCheck(player, 'Really Stupid', log_entry.result)
            if log_entry.result != ActionResult.SUCCESS:
                log_entry = next(cur_log_entries, None)
                if log_entry:
                    validate_log_entry(log_entry, RerollEntry, player.team.team_type)
                    cmd = next(cmds)
                    if isinstance(cmd, ProRerollCommand):
                        if log_entry.result == ActionResult.SUCCESS:
                            yield Reroll(log_entry.team, 'Pro')
                            log_entry = next(cur_log_entries)
                            board.stupidity_test(player, log_entry.result)
                            yield ConditionCheck(player, 'Really Stupid', log_entry.result)
                    elif isinstance(cmd, RerollEntry):
                        board.use_reroll(player.team.team_type)
                        yield Reroll(cmd.team, 'Team Reroll')
                    else:
                        raise ValueError("No RerollCommand to go with RerollEntry")
        if unused:
            unused.log_entries = cur_log_entries

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

        stupid_unused = ReturnWrapper()
        for event in self.__process_stupidity(player, cmd, cmds, move_log_entries, log_entries, board, stupid_unused):
            if isinstance(event, ConditionCheck):
                failed_movement = event.result != ActionResult.SUCCESS
            yield event
        move_log_entries = stupid_unused.log_entries

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
                        if log_entry.team != player.team.team_type:
                            # We have a timeout and play changed - which we have no other way of finding!
                            yield from board.change_turn(log_entry.team, log_entry.reason)
                            move_log_entries = self.__next_generator(log_entries)
                            continue
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
                                board.use_reroll(player.team.team_type)
                                yield Reroll(cmd.team, 'Team Reroll')
                        elif isinstance(log_entry, SkillEntry) and log_entry.skill == Skills.DODGE:
                            validate_log_entry(log_entry, SkillEntry, player.team.team_type)
                            yield Reroll(cmd.team, 'Dodge')
                        elif isinstance(log_entry, ArmourValueRollEntry):
                            yield from self.__handle_armour_roll(log_entry, move_log_entries, player, board)
                        else:
                            cmd = next(cmds)
                            if not isinstance(cmd, DeclineRerollCommand):
                                raise ValueError("No DeclineRerollCommand to go with failed movement action")
                            if board.rerolls[player.team.team_type.value] > 0:
                                cmd = next(cmds)
                                if not isinstance(cmd, BlockDiceChoiceCommand):
                                    raise ValueError("No BlockDiceChoiceCommand? to go with DeclineRerollCommand")
                            break

            if target_space == board.get_ball_position() and not pickup_entry and not failed_movement:
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
                    yield from self.__process_ball_movement(move_log_entries, player, board)
                else:
                    board.set_ball_carrier(player)
                pickup_entry = None

            start_space = target_space

        if turnover:
            yield from board.change_turn(player.team.team_type, turnover)

        if unused:
            unused.log_entries = move_log_entries

    def __process_pass(self, player, cmd, cmds, log_entries, board):
        throw_log_entry = next(log_entries)
        validate_log_entry(throw_log_entry, ThrowEntry, player.team.team_type, player.number)
        throw_command = cmd
        yield Pass(player, throw_command.position, throw_log_entry.result, board)
        if throw_log_entry.result == ThrowResult.FUMBLE:
            while True:
                scatter_entry = next(log_entries)
                start_position = board.get_ball_position()
                ball_position = start_position.scatter(scatter_entry.direction)
                yield Bounce(start_position, ball_position, scatter_entry.direction, board)
                board.set_ball_position(ball_position)
                contents = board.get_position(ball_position)
                if not contents:
                    break
                if board.is_prone(contents):
                    # Prone players can't catch!
                    continue
                catch_entry = next(log_entries)
                if catch_entry.result == ActionResult.SUCCESS:
                    board.set_ball_carrier(contents)
                    break
                # Else they failed so bounce again
        _ = next(cmds)  # XXX: Throw away the next command - cmd_type=13 from the opposition with no other data

    def __process_ball_movement(self, log_entries, player, board):
        log_entry = None
        previous_entry = None
        previous_ball_position = board.get_ball_position()
        turn_over = None
        while True:
            previous_entry = log_entry
            log_entry = next(log_entries, None)
            if isinstance(log_entry, TurnOverEntry):
                validate_log_entry(log_entry, TurnOverEntry, player.team.team_type)
                turn_over = board.change_turn(log_entry.team, log_entry.reason)
            elif isinstance(log_entry, BounceLogEntry):
                old_ball_position = board.get_ball_position()
                if isinstance(previous_entry, BounceLogEntry) and board.get_position(old_ball_position) \
                   and not board.get_ball_carrier():
                    # We sometimes get odd double results where there's two bounces but no catch attempt
                    # but actually the ball just did the second bounce
                    old_ball_position = previous_ball_position
                ball_position = old_ball_position.scatter(log_entry.direction)
                if ball_position.x < 0 or ball_position.x >= PITCH_WIDTH \
                   or ball_position.y < 0 or ball_position.y >= PITCH_LENGTH:
                    ball_position = OFF_PITCH_POSITION
                else:
                    board.set_ball_position(ball_position)
                yield Bounce(old_ball_position, ball_position, log_entry.direction, board)
                if ball_position == OFF_PITCH_POSITION:
                    # Continue to find the throw-in
                    continue
                elif board.get_position(ball_position):
                    # Bounced to an occupied space, so we need to continue
                    previous_ball_position = old_ball_position
                else:
                    # Bounced to an empty space
                    break
            elif isinstance(log_entry, CatchEntry):
                if log_entry.result == ActionResult.SUCCESS:
                    board.set_ball_carrier(self.get_team(log_entry.team).get_player_by_number(log_entry.player))
                    break
                # Else it bounces again
            elif isinstance(log_entry, ThrowInDirectionLogEntry):
                distance_entry = next(log_entries)
                ball_position = previous_ball_position.throwin(log_entry.direction, distance_entry.distance)
                board.set_ball_position(ball_position)
                yield ThrowIn(previous_ball_position, ball_position, log_entry.direction, distance_entry.distance,
                              board)
            else:
                raise ValueError("Expected one of TurnOverEntry, BounceLogEntry, CatchEntry or "
                                 f"ThrowInDirectionLogEntry but got {type(log_entry).__name__}")
        if turn_over:
            yield from turn_over


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
        raise ValueError(f"Expected {expected_type.__name__} but got {type(log_entry).__name__}")
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


def calculate_pushbacks(blocker_coords, old_coords, board):
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
    return [coord for coord in possible_coords if coord.x >= 0 and coord.x <= LAST_COLUMN_IDX
            and coord.y >= 0 and coord.y <= FAR_ENDZONE_IDX and not board.get_position(coord)]


def calculate_pushback(blocker_coords, old_coords, board):
    return calculate_pushbacks(blocker_coords, old_coords, board)[0]
