# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

import sqlite3
import os.path
from collections import namedtuple
from enum import Enum, auto
from . import Peekable, other_team, CoinToss, TeamType, ActionResult, BlockResult, Skills, InjuryRollResult, \
    scatter, throwin, KickoffEvent, Role, ThrowResult, _norths, _souths, \
    PITCH_LENGTH, PITCH_WIDTH, LAST_COLUMN_IDX, NEAR_ENDZONE_IDX, FAR_ENDZONE_IDX, OFF_PITCH_POSITION
from .command import *
from .log import WeatherLogEntry, parse_log_entries, MatchLogEntry, StupidEntry, DodgeEntry, SkillEntry, \
    PickupEntry, TentacledEntry, RerollEntry, TurnOverEntry, BounceLogEntry, FoulAppearanceEntry, LeapEntry, \
    ThrowInDirectionLogEntry, CatchEntry, KORecoveryEntry, ThrowEntry, GoingForItEntry, WildAnimalEntry, \
    SkillRollEntry, ApothecaryLogEntry, LeaderRerollEntry, SpellEntry, ThrowTeammateEntry, LandingEntry, \
    ArmourValueRollEntry, AlwaysHungryEntry
from .state import GameState
from .state import StartTurn, EndTurn, WeatherTuple, AbandonMatch, EndMatch  # noqa: F401 - these are for export
from .teams import create_team


class ActionType(Enum):
    ALWAYS_HUNGRY = auto()
    CATCH = auto()
    DODGE = auto()
    FOUL_APPEARANCE = auto()
    GOING_FOR_IT = auto()
    LANDING = auto()
    LEAP = auto()
    PRO = auto()
    REALLY_STUPID = auto()
    SPELL_HIT = auto()
    WILD_ANIMAL = auto()


MatchEvent = namedtuple('Match', [])
CoinTossEvent = namedtuple('CoinToss', ['toss_team', 'toss_choice', 'toss_result', 'role_team', 'role_choice'])
TeamSetupComplete = namedtuple('TeamSetupComplete', ['team', 'player_positions'])
SetupComplete = namedtuple('SetupComplete', ['board'])
Kickoff = namedtuple('Kickoff', ['target', 'scatter_direction', 'scatter_distance', 'board'])
KickoffEventTuple = namedtuple('KickoffEvent', ['result'])
Movement = namedtuple('Movement', ['player', 'source_space', 'target_space', 'board'])
FailedMovement = namedtuple('FailedMovement', ['player', 'source_space', 'target_space'])
Action = namedtuple('Action', ['player', 'action', 'result', 'board'])
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
DivingTackle = namedtuple('DivingTackle', ['player', 'target_space'])
Pickup = namedtuple('Pickup', ['player', 'position', 'result'])
Pass = namedtuple('Pass', ['player', 'target', 'result', 'board'])
ThrowTeammate = namedtuple('ThrowTeammate', ['player', 'thrown_player', 'target', 'result', 'board'])
Handoff = namedtuple('Handoff', ['player', 'target', 'board'])
Interception = namedtuple('Interception', ['player', 'result', 'board'])
PlayerDown = namedtuple('PlayerDown', ['player'])
Tentacle = namedtuple('Tentacle', ['dodging_player', 'tentacle_player', 'result'])
Skill = namedtuple('Skill', ['player', 'skill'])
SkillRoll = namedtuple('SkillRoll', ['player', 'skill', 'result', 'board'])
Reroll = namedtuple('Reroll', ['team', 'type'])
Bounce = namedtuple('Bounce', ['start_space', 'end_space', 'scatter_direction', 'board'])
Scatter = namedtuple('Scatter', ['start_space', 'end_space', 'board'])
ThrowIn = namedtuple('ThrowIn', ['start_space', 'end_space', 'direction', 'distance', 'board'])
Touchdown = namedtuple('Touchdown', ['player', 'board'])
Touchback = namedtuple('Touchback', ['player', 'board'])
Spell = namedtuple('Spell', ['target', 'spell', 'board'])

END_REASON_TOUCHDOWN = 'Touchdown!'
END_REASON_ABANDON = 'Abandon Match'


def create_replay(db_path, log_path):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"No replay database file at {db_path}")
    db = sqlite3.connect(db_path)
    home_team = create_team(db, TeamType.HOME)
    away_team = create_team(db, TeamType.AWAY)
    commands = create_commands(db)
    log_entries = parse_log_entries(log_path)
    replay = Replay(home_team, away_team, commands, log_entries)
    replay.validate()
    return replay


class Replay:
    def __init__(self, home_team, away_team, commands, log_entries):
        self.home_team = home_team
        self.away_team = away_team
        self.__commands = commands
        self.__log_entries = log_entries
        self.__generator = self.__default_generator

    def validate(self):
        log_entry = self.__log_entries[1]

        if type(log_entry) is not MatchLogEntry:
            raise ValueError("Log did not start with MatchLog entry")
        if log_entry.home_name != self.home_team.name:
            raise ValueError("Home team mismatch between replay and log - got "
                             f"{log_entry.home_name} expected {self.home_team.name}")
        if log_entry.away_name != self.away_team.name:
            raise ValueError("Away team mismatch between replay and log - got "
                             f"{log_entry.away_name} expected {self.away_team.name}")
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

    def __default_generator(self, data):
        return Peekable(x for x in data)

    def set_generator(self, generator):
        if generator:
            self.__generator = generator
        else:
            self.__generator = self.__default_generator

    def events(self):
        log_entries = self.__generator(log_entry for log_entry in self.__log_entries)
        cmds = self.__generator(cmd for cmd in self.__commands if not cmd.is_verbose)

        randomisation = next(log_entries)
        yield MatchEvent()

        _ = next(log_entries)  # Dispose of match entry
        toss_cmd = find_next_known_command(cmds)
        toss_log = next(log_entries)
        role_cmd = find_next_known_command(cmds)
        role_log = next(log_entries)
        toss_team = toss_cmd.team if toss_cmd.team != TeamType.HOTSEAT else randomisation.team
        if toss_team != toss_log.team or toss_cmd.choice != toss_log.choice:
            raise ValueError(f"Mismatch in toss details - {toss_team} {toss_cmd.choice} "
                             f"vs {toss_log.team} {toss_log.choice}")
        if role_cmd.team == TeamType.HOTSEAT:
            role_team = randomisation.team if toss_log.choice == randomisation.result \
                else other_team(randomisation.result)
        else:
            role_team = role_cmd.team
        if role_team != role_log.team or role_cmd.choice != role_log.choice:
            raise ValueError(f"Mismatch in role details - {role_team} {role_cmd.choice} "
                             f"vs {role_log.team} {role_log.choice}")
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
        weather = next(log_entries)
        yield board.set_weather(weather.result)

        yield from self._process_kickoff(cmds, log_entries, board)

        while True:
            drive_ended = False
            while not drive_ended:
                for event in self._process_turn(cmds, log_entries, board):
                    event_type = type(event)
                    if event_type in [Touchdown]:
                        drive_ended = True
                    elif event_type is AbandonMatch or event_type is EndMatch:
                        return
                    yield event
                    if event_type is EndTurn and board.turn == 8 and board.turn_team.team_type != receiver:
                        yield board.halftime()
            yield from self._process_kickoff(cmds, log_entries, board)

    def get_commands(self):
        return self.__commands

    def get_log_entries(self):
        return self.__log_entries

    def _process_kickoff(self, cmds, log_entries, board):
        board.prepare_setup()

        event = next(log_entries)
        while isinstance(event, KORecoveryEntry):
            if event.result == ActionResult.SUCCESS:
                player = self.get_team(event.team).get_player_by_number(event.player)
                board.unset_injured(player)
            event = next(log_entries)

        yield from self._process_team_setup(board.kicking_team, cmds, board)
        yield from self._process_team_setup(board.receiving_team, cmds, board)
        board.setup_complete()
        yield SetupComplete(board)

        kickoff_cmd = find_next_known_command(cmds)
        if isinstance(kickoff_cmd, KickoffCommand):
            kickoff_direction = event
            kickoff_scatter = next(log_entries)
            ball_dest = scatter(kickoff_cmd.position, kickoff_direction.direction, kickoff_scatter.distance)
            board.set_ball_position(ball_dest)
            yield Kickoff(kickoff_cmd.position, kickoff_direction.direction, kickoff_scatter.distance, board)
        elif isinstance(kickoff_cmd, PreKickoffCompleteCommand):
            raise ValueError("Detected kickoff due to timeout - unable to determine position of ball")
        else:
            raise ValueError(f"Unexpected command type at kickoff: {type(kickoff_cmd).__name__}")

        kickoff_event = next(log_entries)
        kickoff_result = kickoff_event.result
        yield KickoffEventTuple(kickoff_result)
        ball_bounces = True
        if kickoff_result == KickoffEvent.PERFECT_DEFENCE:
            yield from self._process_team_setup(board.kicking_team, cmds, board)
            board.setup_complete()
            yield SetupComplete(board)
        elif kickoff_result == KickoffEvent.HIGH_KICK:
            high_kick_catch = next(log_entries)
            catcher = self.get_team(high_kick_catch.team).get_player_by_number(high_kick_catch.player)
            old_position = catcher.position
            new_position = board.get_ball_position()
            board.reset_position(old_position)
            board.set_position(new_position, catcher)
            if high_kick_catch.result == ActionResult.SUCCESS:
                board.set_ball_carrier(catcher)
                ball_bounces = False
            yield Movement(catcher, old_position, new_position, board)
            yield Action(catcher, ActionType.CATCH, high_kick_catch.result, board)
        elif kickoff_result == KickoffEvent.CHEERING_FANS or kickoff_result == KickoffEvent.BRILLIANT_COACHING:
            # XXX: We need to check reroll log events to identify who got the free reroll
            pass
        elif kickoff_result == KickoffEvent.CHANGING_WEATHER:
            while isinstance(log_entries.peek(), WeatherLogEntry):
                weather = next(log_entries)  # Sometimes this duplicates, but we don't care
            yield board.set_weather(weather.result)
        elif kickoff_result == KickoffEvent.QUICK_SNAP:
            board.quick_snap()
            yield from self._process_turn(cmds, log_entries, board, False)
        elif kickoff_result == KickoffEvent.BLITZ:
            board.blitz()
            yield from self._process_turn(cmds, log_entries, board, False)
        elif kickoff_result == KickoffEvent.PITCH_INVASION:
            raise NotImplementedError("Cannot process 'Pitch Invasion' event because injured players aren't identified")
        else:
            raise NotImplementedError(f"{kickoff_result} not yet implemented")

        yield from board.kickoff()

        half_pitch_length = PITCH_LENGTH // 2

        target_half = kickoff_cmd.position.y // half_pitch_length
        landed_half = ball_dest.y // half_pitch_length

        touchback = board.get_ball_position().is_offpitch() or target_half != landed_half

        if ball_bounces:
            if touchback:
                _ = next(log_entries)
            else:
                while isinstance(log_entries.peek(), BounceLogEntry):
                    log_entry = next(log_entries)
                    old_position = ball_dest
                    ball_dest = scatter(ball_dest, log_entry.direction)
                    board.set_ball_position(ball_dest)
                    yield Bounce(old_position, ball_dest, log_entry.direction, board)
                if ball_dest.is_offpitch():
                    touchback = True
        # else
        # TODO: Handle no bounce when it gets caught straight away (but not via "High Kick" event)

        if touchback:
            cmd = next(cmds)
            while isinstance(cmd, PreKickoffCompleteCommand):
                cmd = next(cmds)
            if not isinstance(cmd, TouchbackCommand):
                raise ValueError(f"Expected TouchbackCommand but got {type(cmd).__name__}")
            touchback_player = self.get_team(cmd.team).get_player(cmd.player_idx)
            board.set_ball_carrier(touchback_player)
            yield Touchback(touchback_player, board)

    def _process_team_setup(self, team_type, cmds, board):
        cmd = next(cmds)
        cmd_type = type(cmd)
        team = self.get_team(team_type)
        while cmd_type is not SetupCompleteCommand:
            if cmd_type is not SetupCommand:
                cmd = next(cmds)
                cmd_type = type(cmd)
                continue
            # else…

            player = team.get_player(cmd.player_idx)
            old_coords = player.position
            if player.is_on_pitch():
                board.reset_position(old_coords)

            coords = cmd.position
            space_contents = board.get_position(coords)

            if space_contents and space_contents != player:
                board.set_position(old_coords, space_contents)
            board.set_position(coords, player)
            cmd = next(cmds)
            cmd_type = type(cmd)

        for i in range(PITCH_WIDTH):
            endzone_contents = board[NEAR_ENDZONE_IDX][i]
            if endzone_contents:
                board[NEAR_ENDZONE_IDX][i] = None
                endzone_contents.position = OFF_PITCH_POSITION
            endzone_contents = board[FAR_ENDZONE_IDX][i]
            if endzone_contents:
                board[FAR_ENDZONE_IDX][i] = None
                endzone_contents.position = OFF_PITCH_POSITION
        yield TeamSetupComplete(team_type, team.get_players())

    def _process_turn(self, cmds, log_entries, board, start_next_turn=True):
        cmd = None
        end_reason = None
        prev_cmd_type = None
        cmd_type = None

        while not end_reason:
            prev_cmd_type = cmd_type
            cmd = cmds.peek()
            if cmd is None:
                break
            cmd_type = type(cmd)
            if isinstance(cmd, TargetPlayerCommand):
                targeting_player = self.get_team(cmd.team).get_player(cmd.player_idx)
                target_by_idx = self.get_team(cmd.target_team).get_player(cmd.target_player)
                is_block = targeting_player.team != target_by_idx.team
                if is_block:
                    yield from self._process_block(targeting_player, target_by_idx, cmds, log_entries, board)
                elif not cmd.position.is_offpitch():
                    # Regular throws use 255,255 but throw teammate uses the target coords
                    for event in self._process_throw_teammate(targeting_player, target_by_idx,
                                                              cmds, log_entries, board):
                        if isinstance(event, EndTurn):
                            end_reason = event.reason
                        else:
                            yield event
                else:
                    for event in self._process_throw(targeting_player, target_by_idx, cmds, log_entries, board):
                        if isinstance(event, EndTurn):
                            end_reason = event.reason
                        else:
                            yield event
            elif isinstance(cmd, MovementCommand):
                player = self.get_team(cmd.team).get_player(cmd.player_idx)
                # We stop when the movement stops, so the returned command is the EndMovementCommand
                yield from self._process_movement(player, cmds, log_entries, board)
            elif isinstance(cmd, SpellCommand):
                yield from self._process_spell(cmds, log_entries, board)
            elif cmd_type is Command or cmd_type is PreKickoffCompleteCommand:
                next(cmds)
                continue
            elif cmd_type is DeclineRerollCommand or (cmd_type is DiceChoiceCommand
                                                      and prev_cmd_type is DeclineRerollCommand):
                # FIXME: We should be handling these, but it's not always clear how they associate with events
                next(cmds)
                continue
            elif cmd_type is EndTurnCommand:
                next(cmds)
                end_reason = 'End Turn'
            elif cmd_type is AbandonMatchCommand:
                next(cmds)
                end_reason = END_REASON_ABANDON
            else:
                raise NotImplementedError(f"No handling for {cmd}")

            if board.is_touchdown_state():
                player = board.get_ball_carrier()
                board.touchdown(player)
                yield Touchdown(player, board)
                end_reason = END_REASON_TOUCHDOWN

        if end_reason == END_REASON_ABANDON:
            yield from board.abandon_match(cmd.team)
        else:
            yield from board.end_turn(cmd.team, end_reason)
            if start_next_turn and end_reason != END_REASON_TOUCHDOWN:
                # Touchdowns will be restarted by the setup and kickoff process
                yield from board.start_turn(other_team(cmd.team))

    def _process_action_result(self, log_entry, log_type, cmds, log_entries, player, action_type, board,
                               is_active=True):
        validate_log_entry(log_entry, log_type, player.team.team_type, player.number)
        yield Action(player, action_type, log_entry.result, board)
        if log_entry.result != ActionResult.SUCCESS and player.team == board.turn_team:
            actions, new_result = self._process_action_reroll(cmds, log_entries, player, board, is_active=is_active)
            yield from actions
            if new_result:
                yield Action(player, action_type, new_result, board)

    def __process_reroll_command(self, log_entries, player, board):
        actions = []
        reroll_success = False
        team = player.team
        team_type = player.team.team_type
        has_leader_reroll = board.has_leader_reroll(team_type)
        leader = None
        if has_leader_reroll:
            log_entry = next(log_entries)
            validate_log_entry(log_entry, LeaderRerollEntry, team_type)
            leader = team.get_player_by_number(log_entry.player)
            reroll_type = 'Leader Reroll'
        else:
            reroll_type = 'Team Reroll'

        reroll_success = True

        if Skills.LONER in player.skills:
            log_entry = next(log_entries)
            validate_log_entry(log_entry, SkillRollEntry, team_type, player.number)
            actions.append(SkillRoll(player, Skills.LONER, log_entry.result, board))
            reroll_success = log_entry.result == ActionResult.SUCCESS

        if leader:
            board.use_leader_reroll(team_type, leader)
        else:
            board.use_reroll(team_type)
        actions.append(Reroll(team_type, reroll_type))

        if not has_leader_reroll:
            log_entry = next(log_entries)
            validate_log_entry(log_entry, RerollEntry, team_type)
        return reroll_success, actions

    def _process_action_reroll(self, cmds, log_entries, player, board, reroll_skill=None,
                               cancelling_skill=None, modifying_skill=None, is_active=True):
        actions = []
        new_result = None
        reroll_success = False
        if reroll_skill and reroll_skill in player.skills \
           and not any(cancelling_skill in opponent.skills
                       for opponent in board.get_surrounding_players(player.position)):
            log_entry = next(log_entries)
            validate_log_entry(log_entry, SkillEntry, player.team.team_type, player.number)
            actions.append(Reroll(player.team.team_type, reroll_skill.name.title()))
            reroll_success = True
        elif Skills.PRO in player.skills:
            cmd = next(cmds)
            if isinstance(cmd, ProRerollCommand):
                log_entry = next(log_entries)
                validate_log_entry(log_entry, RerollEntry, player.team.team_type, player.number)
                actions.append(Action(player, ActionType.PRO, log_entry.result, board))
                if log_entry.result == ActionResult.SUCCESS:
                    actions.append(Reroll(log_entry.team, 'Pro'))
                    reroll_success = True
                elif is_active:
                    cmd = next(cmds)
                    if not isinstance(cmd, DiceChoiceCommand):
                        raise ValueError("Expected DiceChoiceCommand after ProRerollCommand "
                                         f"but got {type(cmd).__name__}")
        elif board.can_reroll(player.team.team_type):
            cmd = next(cmds)
            if isinstance(cmd, DeclineRerollCommand):
                if is_active:
                    cmd = next(cmds)
                    if not isinstance(cmd, DiceChoiceCommand):
                        raise ValueError("Expected DiceChoiceCommand after DeclineRerollCommand "
                                         f"but got {type(cmd).__name__}")
            elif isinstance(cmd, RerollCommand):
                reroll_success, actions = self.__process_reroll_command(log_entries, player, board)
            elif isinstance(cmd, DiceChoiceCommand):
                # Sometimes we only get cmd_type=19 even though most of the time
                # we get cmd_type=51 for declined reroll
                pass
            else:
                raise ValueError(f"Non-reroll command {type(cmd).__name__} found after failed action")
        if modifying_skill:
            log_entry = next(log_entries)
            validate_log_entry(log_entry, SkillEntry, other_team(player.team.team_type))
        if reroll_success:
            log_entry = next(log_entries)
            new_result = log_entry.result
        return actions, new_result

    def _process_armour_roll(self, player, cmds, roll_entry, log_entries, board):
        validate_log_entry(roll_entry, ArmourValueRollEntry,
                           player.team.team_type, player.number)
        board.set_prone(player)
        yield PlayerDown(player)
        yield ArmourRoll(player, roll_entry.result)
        if roll_entry.result == ActionResult.SUCCESS:
            yield from self._process_injury_roll(player, cmds, log_entries, board)

    def _process_injury_roll(self, player, cmds, log_entries, board):
        injury_roll = next(log_entries)
        if injury_roll.result != InjuryRollResult.STUNNED:
            board.reset_position(player.position)
            board.set_injured(player)
        yield InjuryRoll(player, injury_roll.result)
        if injury_roll.result == InjuryRollResult.INJURED:
            yield from self._process_casualty(player, cmds, log_entries, board)
        elif injury_roll.result == InjuryRollResult.KO:
            yield from self._process_apothecary(player, injury_roll.result, CasualtyResult.NONE,
                                                cmds, log_entries, board)
        # Else they're stunned and we can't do anything

    def _process_casualty(self, player, cmds, log_entries, board):
        casualty_roll = next(log_entries)
        yield Casualty(player, casualty_roll.result)
        yield from self._process_apothecary(player, InjuryRollResult.INJURED, casualty_roll.result,
                                            cmds, log_entries, board)

    def _process_apothecary(self, player, injury, casualty_result, cmds, log_entries, board):
        if player.position.is_offpitch():
            # Assume we're using older rules where apothecaries can't help players in the crowd
            return
        if injury == InjuryRollResult.STUNNED:
            raise ValueError("Apothecary cannot help stunned players")
        if not isinstance(cmds.peek(), ApothecaryCommand):
            # Let them suffer their fate!
            return
        cmd = next(cmds)
        if not isinstance(cmd, ApothecaryCommand):
            raise ValueError(f"Expected ApothecaryCommand after injury but got {type(cmd).__name__}")
        if cmd.team != player.team.team_type or player.team.get_player_number(cmd.player) != player.number:
            raise ValueError(f"Expected ApothecaryCommand for {player.team.team_type} #{player.number} "
                             f"but got {cmd.team} #{player.team.get_player_number(cmd.player)}")
        if not cmd.used:
            # Let them suffer their fate!
            return
        apothecary_log_entry = next(log_entries)
        validate_log_entry(apothecary_log_entry, ApothecaryLogEntry, player.team.team_type, player.number)
        if casualty_result == CasualtyResult.NONE:
            yield Apothecary(player, InjuryRollResult.STUNNED, CasualtyResult.NONE)
            yield InjuryRoll(player, InjuryRollResult.STUNNED)
            return
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
        if cmd.result == CasualtyResult.BADLY_HURT:
            board.unset_injured(player)
        yield Casualty(player, cmd.result)

    def _process_uncontrollable_skills(self, player, cmds, log_entries, board):
        if board.quick_snap_turn:
            return
        yield from self._process_stupidity(player, cmds, log_entries, board)
        yield from self._process_wild_animal(player, cmds, log_entries, board)

    def _process_stupidity(self, player, cmds, log_entries, board):
        if Skills.REALLY_STUPID in player.skills and not board.tested_stupid(player):
            log_entry = next(log_entries)
            validate_log_entry(log_entry, StupidEntry, player.team.team_type, player.number)
            board.stupidity_test(player, log_entry.result)
            yield Action(player, ActionType.REALLY_STUPID, log_entry.result, board)
            if log_entry.result != ActionResult.SUCCESS:
                actions, new_result = self._process_action_reroll(cmds, log_entries, player, board)
                yield from actions
                if new_result:
                    board.stupidity_test(player, new_result)
                    yield Action(player, ActionType.REALLY_STUPID, new_result, board)

    def _process_wild_animal(self, player, cmds, log_entries, board):
        if Skills.WILD_ANIMAL in player.skills and not board.tested_wild_animal(player):
            log_entry = next(log_entries)
            validate_log_entry(log_entry, WildAnimalEntry, player.team.team_type, player.number)
            board.wild_animal_test(player, log_entry.result)
            yield Action(player, ActionType.WILD_ANIMAL, log_entry.result, board)
            if log_entry.result != ActionResult.SUCCESS:
                actions, new_result = self._process_action_reroll(cmds, log_entries, player, board)
                yield from actions
                if new_result:
                    board.wild_animal_test(player, new_result)
                    yield Action(player, ActionType.WILD_ANIMAL, new_result, board)

    def _process_block(self, targeting_player, target_by_idx, cmds, log_entries, board):
        cmd = next(cmds)

        if not isinstance(cmd, TargetPlayerCommand):
            raise ValueError(f"Expected TargetPlayerCommand but got {type(cmd).__name__}")

        cmd = cmds.peek()
        moved = False
        if isinstance(cmd, MovementCommand):
            moved = True
            yield Blitz(targeting_player, target_by_idx)
            moves = self.__get_moves(targeting_player, cmds)
            cmd = next(cmds)
            yield from self.__process_movement_list(targeting_player, moves, cmds, log_entries, board)
            if board.is_prone(targeting_player):
                # Something failed in the block
                return
        else:
            cmd = next(cmds)
            yield from self._process_uncontrollable_skills(targeting_player, cmds, log_entries, board)
            if board.is_prone(targeting_player):
                board.unset_prone(targeting_player)
                yield Blitz(targeting_player, target_by_idx)

        if board.is_wild_animal(targeting_player):
            # If they're wild then they failed their roll
            return

        if not isinstance(cmd, TargetSpaceCommand):
            raise ValueError(f"Expected TargetSpaceCommand but got {type(cmd).__name__}")

        target_by_coords = board.get_position(cmd.position)
        if target_by_coords != target_by_idx:
            raise ValueError(f"Target command targetted {target_by_idx} but {cmd} targetted {target_by_coords}")

        yield from self.__process_block_rolls(targeting_player, target_by_idx, cmds, moved, log_entries, board)

    def __process_block_rolls(self, targeting_player, target_by_idx, cmds, moved,
                              log_entries, board, frenzied_block=False):
        if Skills.FOUL_APPEARANCE in target_by_idx.skills:
            log_entry = next(log_entries)
            yield from self._process_action_result(log_entry, FoulAppearanceEntry, cmds, log_entries,
                                                   targeting_player, ActionType.FOUL_APPEARANCE, board)

        dumped_off = False
        if Skills.DUMP_OFF in target_by_idx.skills and board.get_ball_carrier() == target_by_idx:
            dumped_off = True
            dumpoff_cmd = next(cmds)
            if dumpoff_cmd.team != target_by_idx.team.team_type:
                raise ValueError(f"{target_by_idx} used dump off but command was for {dumpoff_cmd.team}")
            yield from self._process_pass(target_by_idx, cmds, log_entries, board)
        if moved and board.get_distance_moved(targeting_player) >= targeting_player.MA:
            log_entry = next(log_entries)
            success = True
            rerolled = False
            for event in self._process_action_result(log_entry, GoingForItEntry, cmds, log_entries,
                                                     targeting_player, ActionType.GOING_FOR_IT, board):
                yield event
                if isinstance(event, Action):
                    success = event.result == ActionResult.SUCCESS
                elif isinstance(event, Reroll):
                    rerolled = True
            if dumped_off and rerolled:
                log_entry = next(log_entries)
                for event in self._process_action_result(log_entry, GoingForItEntry, cmds, log_entries,
                                                         targeting_player, ActionType.GOING_FOR_IT, board):
                    yield event
                    if isinstance(event, Action):
                        success = event.result == ActionResult.SUCCESS

            if not success:
                log_entry = next(log_entries)
                yield from self._process_armour_roll(targeting_player, cmds, log_entry, log_entries, board)
                log_entry = next(log_entries)
                validate_log_entry(log_entry, TurnOverEntry, targeting_player.team.team_type)
                yield from board.change_turn(targeting_player.team.team_type, log_entry.reason)
                return

        blocking_player = targeting_player
        board.throw_block(blocking_player)
        block_dice = next(log_entries)
        block_choice = next(cmds)
        if isinstance(block_choice, ProRerollCommand):
            reroll = next(log_entries)
            yield Action(blocking_player, ActionType.PRO, reroll.result, board)
            if reroll.result == ActionResult.SUCCESS:
                yield Reroll(reroll.team, 'Pro')
                _ = next(log_entries)  # Burn the random duplication
            elif len(block_dice.results) == 2 and block_dice.results[0] == block_dice.results[1]:
                _ = next(cmds)  # Burn the reroll prompt that shows as a block dice choice
            block_dice = next(log_entries)
            block_choice = next(cmds)
        elif isinstance(block_choice, RerollCommand):
            _, actions = self.__process_reroll_command(log_entries, blocking_player, board)
            yield from actions
            block_dice = next(log_entries)
            block_choice = next(cmds)
        chosen_block_dice = block_dice.results[block_choice.dice_idx]
        yield Block(blocking_player, target_by_idx,
                    block_dice.results, chosen_block_dice)

        if chosen_block_dice == BlockResult.BOTH_DOWN and Skills.JUGGERNAUT in blocking_player.skills:
            jugg_cmd = next(cmds)
            if jugg_cmd.team != blocking_player.team.team_type \
               or blocking_player.team.get_player_number(jugg_cmd.player_idx) != blocking_player.number:
                raise ValueError("Expected ApothecaryCommand for "
                                 f"{blocking_player.team.team_type} #{blocking_player.number} but got "
                                 f"{jugg_cmd.team} #{blocking_player.team.get_player_number(jugg_cmd.player_idx)}")
            if jugg_cmd.choice:
                chosen_block_dice = BlockResult.PUSHED
                skill_entry = next(log_entries)
                validate_skill_log_entry(skill_entry, blocking_player, Skills.JUGGERNAUT)
                yield Skill(blocking_player, Skills.JUGGERNAUT)
                attacker_avoided = True
                defender_avoided = True

        block_position = target_by_idx.position

        if chosen_block_dice == BlockResult.PUSHED or chosen_block_dice == BlockResult.DEFENDER_DOWN \
           or chosen_block_dice == BlockResult.DEFENDER_STUMBLES:
            origin_coords = blocking_player.position
            old_coords = target_by_idx.position
            pushbacks = calculate_pushbacks(origin_coords, old_coords, board)
            board.reset_position(old_coords)

            if len(pushbacks) != 1 or Skills.SIDE_STEP in target_by_idx.skills:
                pushing_player = blocking_player
                pushed_player = target_by_idx
                pushed_back = False
                cmd = None

                while isinstance(cmds.peek(), SideStepCommand):
                    cmd = next(cmds)
                    if cmd.sidestepped:
                        log_entry = next(log_entries)
                        sidestepping_player = self.get_team(cmd.defender_team).get_player(cmd.defender_idx)
                        validate_skill_log_entry(log_entry, sidestepping_player, Skills.SIDE_STEP)
                        yield Skill(sidestepping_player, Skills.SIDE_STEP)

                while isinstance(cmds.peek(), PushbackCommand):
                    pushed_back = True
                    cmd = next(cmds)
                    new_coords = cmd.position
                    dest_content = board.get_position(new_coords)
                    origin_coords = pushed_player.position
                    board.set_position(new_coords, pushed_player)
                    yield Pushback(pushing_player, pushed_player, old_coords, new_coords, board)
                    if dest_content:
                        pushing_player = pushed_player
                        pushed_player = dest_content
                        old_coords = new_coords

                if not pushed_back:
                    raise ValueError("Expected PushbackCommand after "
                                     f"{chosen_block_dice} but got {type(cmds.peek()).__name__}")
            else:
                new_coords = pushbacks[0]
                board.set_position(new_coords, target_by_idx)
                yield Pushback(blocking_player, target_by_idx, old_coords, new_coords, board)

            can_fend = Skills.FEND in target_by_idx.skills \
                and (not moved or Skills.JUGGERNAUT not in blocking_player.skills)
            if can_fend:
                skill_entry = next(log_entries)
                validate_skill_log_entry(skill_entry, target_by_idx, Skills.FEND)
                yield Skill(target_by_idx, Skills.FEND)

            follow_up = False

            if Skills.FRENZY in blocking_player.skills and Skills.FEND not in target_by_idx.skills:
                follow_up = True
            elif isinstance(cmds.peek(), FollowUpChoiceCommand):
                cmd = next(cmds)
                follow_up = cmd.choice
            elif can_fend:
                follow_up = False
            else:
                raise ValueError(f"Unexpected follow-up situation - next command is {type(cmds.peek()).__name__}")

            if follow_up:
                old_coords = blocking_player.position
                board.reset_position(old_coords)
                board.set_position(block_position, blocking_player)
                yield FollowUp(blocking_player, target_by_idx, old_coords, block_position, board)

        attacker_avoided = False
        defender_avoided = False

        if chosen_block_dice == BlockResult.DEFENDER_STUMBLES and Skills.DODGE in target_by_idx.skills:
            skill_entry = next(log_entries)
            validate_skill_log_entry(skill_entry, target_by_idx, Skills.DODGE)
            yield DodgeBlock(blocking_player, target_by_idx)
            defender_avoided = True
        elif chosen_block_dice == BlockResult.BOTH_DOWN:
            if Skills.BLOCK in blocking_player.skills:
                skill_entry = next(log_entries)
                validate_skill_log_entry(skill_entry, blocking_player, Skills.BLOCK)
                yield BlockBothDown(blocking_player)
                attacker_avoided = True
            if Skills.BLOCK in target_by_idx.skills:
                skill_entry = next(log_entries)
                validate_skill_log_entry(skill_entry, target_by_idx, Skills.BLOCK)
                yield BlockBothDown(target_by_idx)
                defender_avoided = True

        attacker_down = False
        if (chosen_block_dice == BlockResult.ATTACKER_DOWN
            or chosen_block_dice == BlockResult.BOTH_DOWN) \
                and not attacker_avoided:
            attacker_down = True
            armour_entry = next(log_entries)
            yield from self._process_armour_roll(blocking_player, cmds, armour_entry, log_entries, board)

        ball_bounces = False
        if target_by_idx.position.is_offpitch():
            yield from self._process_injury_roll(target_by_idx, cmds, log_entries, board)
            if board.get_ball_carrier() == target_by_idx:
                board.set_ball_position(block_position)  # Drop the ball so the throw-in works
                ball_bounces = True
        elif (chosen_block_dice == BlockResult.DEFENDER_DOWN or chosen_block_dice == BlockResult.DEFENDER_STUMBLES
              or chosen_block_dice == BlockResult.BOTH_DOWN) \
                and not defender_avoided:
            armour_entry = next(log_entries)
            pushed_into_ball = target_by_idx.position == board.get_ball_position()
            yield from self._process_armour_roll(target_by_idx, cmds, armour_entry, log_entries, board)

            if board.get_ball_carrier() == target_by_idx or pushed_into_ball:
                ball_bounces = True

        next_cmd = cmds.peek()
        if isinstance(next_cmd, MovementCommand) \
                and board.teams[next_cmd.team.value].get_player(next_cmd.player_idx) == targeting_player:
            yield from self._process_movement(blocking_player, cmds, log_entries, board)

        if ball_bounces:
            yield from self._process_ball_movement(cmds, log_entries, board)

        if attacker_down:
            log_entry = next(log_entries)
            validate_log_entry(log_entry, TurnOverEntry, blocking_player.team.team_type)
            yield from board.change_turn(blocking_player.team.team_type, log_entry.reason)
        elif not frenzied_block and Skills.FRENZY in blocking_player.skills and \
                (defender_avoided or chosen_block_dice == BlockResult.PUSHED):
            if board.get_distance_moved(targeting_player) >= targeting_player.MA + 2:
                # Can't Frenzy when we hit our GFI limit
                return
            log_entry = next(log_entries)
            validate_skill_log_entry(log_entry, targeting_player, Skills.FRENZY)
            yield Skill(targeting_player, Skills.FRENZY)
            yield from self.__process_block_rolls(targeting_player, target_by_idx, cmds, moved,
                                                  log_entries, board, True)

    def _process_throw(self, player, target_by_idx, cmds, log_entries, board):
        cmd = next(cmds)
        if not isinstance(cmd, TargetPlayerCommand):
            raise ValueError(f"Expected TargetPlayerCommand but got {type(cmd).__name__}")
        failed_throw = False
        for event in self._process_uncontrollable_skills(player, cmds, log_entries, board):
            if isinstance(event, Action):
                failed_throw = event.result != ActionResult.SUCCESS
            yield event

        if failed_throw:
            return

        if isinstance(cmds.peek(), MovementCommand):
            yield from self._process_movement(player, cmds, log_entries, board)
        pass_cmd = cmds.peek()
        player_pos = player.position
        if abs(pass_cmd.x - player_pos.x) > 1 or abs(pass_cmd.y - player_pos.y) > 1:
            yield from self._process_pass(player, cmds, log_entries, board)
            if not board.get_ball_carrier():
                log_entry = next(log_entries)
                validate_log_entry(log_entry, TurnOverEntry, player.team.team_type)
                yield EndTurn(player.team, board.turn, log_entry.reason, board)
        else:
            # Else hand-off - doesn't have the pass part, just the catch
            pass_cmd = next(cmds)
            yield Handoff(player, target_by_idx, board)
            catch_entry = next(log_entries)
            target_by_coords = board.get_position(pass_cmd.position)
            if target_by_coords != target_by_idx:
                raise ValueError(f"Expected catch for {target_by_coords.team_type} #{target_by_coords.number} "
                                 f"but got {target_by_idx.team_type} #{target_by_idx.number}")
            validate_log_entry(catch_entry, CatchEntry, pass_cmd.team, target_by_coords.number)
            if catch_entry.result == ActionResult.SUCCESS:
                board.set_ball_carrier(target_by_idx)
                yield Action(target_by_idx, ActionType.CATCH, catch_entry.result, board)
            else:
                log_entry = next(log_entries)
                validate_log_entry(log_entry, TurnOverEntry, player.team.team_type)
                yield Action(target_by_idx, ActionType.CATCH, catch_entry.result, board)
                yield EndTurn(player.team, board.turn, log_entry.reason, board)

    def _process_throw_teammate(self, player, target_by_idx, cmds, log_entries, board):
        if Skills.THROW_TEAMMATE not in player.skills:
            raise ValueError(f"Throw teammate attempted by {player.name} without Throw Teammate skill")
        if Skills.RIGHT_STUFF not in target_by_idx.skills:
            raise ValueError(f"Throw teammate attempted on {target_by_idx.name} without Right Stuff skill")

        throw_command = next(cmds)

        failed_throw = False
        for event in self._process_uncontrollable_skills(player, cmds, log_entries, board):
            if isinstance(event, Action):
                failed_throw = event.result != ActionResult.SUCCESS
            yield event

        if failed_throw:
            return

        if Skills.ALWAYS_HUNGRY in player.skills:
            log_entry = next(log_entries)
            success = True
            for event in self._process_action_result(log_entry, AlwaysHungryEntry, cmds, log_entries,
                                                     player, ActionType.ALWAYS_HUNGRY, board):
                yield event
                if isinstance(event, Action):
                    success = event.result == ActionResult.SUCCESS
            if not success:
                raise NotImplementedError("Failed AlwaysHungry check not seen or implemented")

        pickup_command = next(cmds)
        if not isinstance(pickup_command, TargetSpaceCommand):
            raise ValueError(f"Expected TargetSpaceCommand but got {pickup_command.__name__}")

        target_by_coords = board.get_position(pickup_command.position)
        if target_by_coords != target_by_idx:
            raise ValueError(f"Target command targetted {target_by_idx} but {pickup_command} targetted "
                             f"{target_by_coords}")

        throw_log_entry = next(log_entries)
        validate_log_entry(throw_log_entry, ThrowTeammateEntry, player.team.team_type, player.number)
        result = throw_log_entry.result
        yield ThrowTeammate(player, target_by_idx, throw_command.position, result, board)

        # Only check rerolls for fumbles, because Accurate isn't possible
        if throw_log_entry.result == ThrowResult.FUMBLE:
            actions, result = self._process_action_reroll(cmds, log_entries, player, board)
            yield from actions
            if result is not None:
                yield ThrowTeammate(player, target_by_idx, throw_command.position, result, board)

        if result == ThrowResult.INACCURATE_PASS:
            scatter_1 = next(log_entries)
            scatter_2 = next(log_entries)
            scatter_3 = next(log_entries)
            landing_position = scatter(throw_command.position, scatter_1.direction)
            landing_position = scatter(landing_position, scatter_2.direction)
            landing_position = scatter(landing_position, scatter_3.direction)
            board.reset_position(pickup_command.position)
            board.set_position(landing_position, target_by_idx)
            yield Scatter(throw_command.position, landing_position, board)
        # else it was a fumble and players lands where they started

        landing_entry = next(log_entries)
        validate_log_entry(landing_entry, LandingEntry, target_by_idx.team.team_type, target_by_idx.number)
        yield Action(target_by_idx, ActionType.LANDING, landing_entry.result, board)

        if not landing_entry.result == ActionResult.SUCCESS:
            armour_entry = next(log_entries)
            yield from self._process_armour_roll(target_by_idx, cmds, armour_entry, log_entries, board)

    def _process_movement(self, player, cmds, log_entries, board):
        yield from self.__process_movement_list(player, self.__get_moves(player, cmds), cmds, log_entries, board)

    def __get_moves(self, player, cmds):
        moves = []
        # We can't just use "while true" and check for EndMovementCommand because a blitz is
        # movement followed by a Block without an EndMovementCommand
        while isinstance(cmds.peek(), MovementCommand):
            cmd = next(cmds)
            team = self.get_team(cmd.team)
            idx_player = team.get_player(cmd.player_idx)
            if self.get_team(cmd.team).get_player(cmd.player_idx) != player:
                raise ValueError(f"Expected movement for {player.team.team_type} #{player.number} "
                                 f"but got {team.team_type} #{idx_player.number}")
            moves.append(cmd)
            if isinstance(cmd, EndMovementCommand):
                break
        return moves

    def __process_movement_list(self, player, moves, cmds, log_entries, board):
        failed_movement = False
        pickup_entry = None
        diving_tackle_entry = None
        start_space = player.position
        turnover = False
        is_prone = board.is_prone(player)
        is_ball_carrier = board.get_ball_carrier() == player

        for event in self._process_uncontrollable_skills(player, cmds, log_entries, board):
            if isinstance(event, Action):
                failed_movement = event.result != ActionResult.SUCCESS
            yield event
        leap = False

        for movement in moves:
            target_space = movement.position
            if (abs(target_space.x - start_space.x) > 1 or abs(target_space.y - start_space.y) > 1) and not leap:
                raise ValueError(f"Unexpected large move for {player.name} from {start_space} to {target_space}")
            if failed_movement:
                if leap:
                    leap = False
                    board.set_position(target_space, player)
                yield FailedMovement(player, start_space, target_space)
                start_space = target_space
                continue

            leap = False

            if not failed_movement and is_dodge(board, player, target_space):
                while True:
                    log_entry = next(log_entries, None)
                    if not log_entry:
                        break
                    elif isinstance(log_entry, PickupEntry):
                        validate_log_entry(log_entry, PickupEntry, player.team.team_type, player.number)
                        pickup_entry = log_entry
                        break
                    elif isinstance(log_entry, DodgeEntry):
                        validate_log_entry(log_entry, DodgeEntry, player.team.team_type, player.number)
                        yield Action(player, ActionType.DODGE, log_entry.result, board)
                        if log_entry.result == ActionResult.SUCCESS:
                            failed_movement = False
                            break
                        failed_movement = True
                        modifying_skill = Skills.DIVING_TACKLE if diving_tackle_entry else None
                        actions, new_result = self._process_action_reroll(cmds, log_entries, player, board,
                                                                          Skills.DODGE, modifying_skill=modifying_skill,
                                                                          cancelling_skill=Skills.TACKLE)
                        yield from actions
                        if new_result:
                            yield Action(player, ActionType.DODGE, new_result, board)
                            failed_movement = new_result != ActionResult.SUCCESS
                        if failed_movement:
                            log_entry = next(log_entries)
                            yield from self._process_armour_roll(player, cmds, log_entry, log_entries, board)
                            turnover = True
                            break
                        break
                    elif isinstance(log_entry, TentacledEntry):
                        surrounding_players = board.get_surrounding_players(start_space)
                        if not any(Skills.TENTACLES in player.skills for player in surrounding_players):
                            raise ValueError("Got TentacledEntry but none of the surrounding players have tentacles!")
                        validate_log_entry(log_entry, TentacledEntry, player.team.team_type, player.number)
                        attacker = self.get_team(log_entry.attacking_team)\
                                       .get_player_by_number(log_entry.attacking_player)
                        yield Tentacle(player, attacker, log_entry.result)
                        failed_movement = log_entry.result == ActionResult.FAILURE
                        if log_entry.result == ActionResult.FAILURE:
                            actions, new_result = self._process_action_reroll(cmds, log_entries, player, board)
                            yield from actions
                            if new_result:
                                yield Tentacle(player, attacker, new_result)
                                failed_movement = new_result == ActionResult.FAILURE
                        if failed_movement:
                            break
                    elif isinstance(log_entry, TurnOverEntry):
                        if log_entry.team != player.team.team_type:
                            # We have a timeout and play changed - which we have no other way of finding!
                            yield from board.change_turn(log_entry.team, log_entry.reason)
                            continue
                        else:
                            raise ValueError("Unexpected in-line TurnOver entry during movement")
                    elif isinstance(log_entry, SkillEntry) and log_entry.skill == Skills.DIVING_TACKLE:
                        diving_tackle_entry = log_entry
                        continue
                    elif isinstance(log_entry, LeapEntry):
                        leap = True
                        validate_log_entry(log_entry, LeapEntry, player.team.team_type, player.number)
                        yield Action(player, ActionType.LEAP, log_entry.result, board)
                        if log_entry.result == ActionResult.SUCCESS:
                            failed_movement = False
                            break
                        failed_movement = True
                        actions, new_result = self._process_action_reroll(cmds, log_entries, player, board,
                                                                          Skills.DODGE)
                        yield from actions
                        if new_result:
                            yield Action(player, ActionType.DODGE, new_result, board)
                            failed_movement = new_result != ActionResult.SUCCESS
                        if failed_movement:
                            log_entry = next(log_entries)
                            yield from self._process_armour_roll(player, cmds, log_entry, log_entries, board)
                            turnover = True
                            break
                    else:
                        raise ValueError("Looking for dodge-related log entries but got "
                                         f"{type(log_entry).__name__}")

            if board.get_distance_moved(player) >= player.MA:
                log_entry = next(log_entries)
                result = log_entry.result
                for event in self._process_action_result(log_entry, GoingForItEntry, cmds, log_entries,
                                                         player, ActionType.GOING_FOR_IT, board):
                    yield event
                    if isinstance(event, Action):
                        result = event.result
                if result == ActionResult.FAILURE:
                    failed_movement = True
                    yield from self._process_armour_roll(player, cmds, next(log_entries), log_entries, board)
                    turnover = True

            if leap:
                continue
            elif target_space == board.get_ball_position() and not pickup_entry:
                if not failed_movement:
                    log_entry = next(log_entries)
                    validate_log_entry(log_entry, PickupEntry, player.team.team_type, player.number)
                    pickup_entry = log_entry
                elif turnover:
                    # They went splat on the ball
                    yield from self._process_ball_movement(cmds, log_entries, board)
            else:
                target_contents = board.get_position(target_space)
                if target_contents and target_contents != player:
                    raise ValueError(f"{player} tried to move to occupied space {target_space}")

            if not failed_movement:
                if is_prone:
                    board.unset_prone(player)
                    is_prone = False
                board.move(player, start_space, target_space)
                yield Movement(player, start_space, target_space, board)
            elif turnover:
                board.move(player, start_space, target_space)
                yield FailedMovement(player, start_space, target_space)
                if is_ball_carrier:
                    yield from self._process_ball_movement(cmds, log_entries, board)
                    board.set_ball_carrier(None)
            else:
                # Failure due to Tentacles etc
                if is_prone:
                    board.unset_prone(player)
                    is_prone = False
                yield FailedMovement(player, start_space, target_space)

            if diving_tackle_entry:
                team = self.get_team(diving_tackle_entry.team)
                diving_player = team.get_player_by_number(diving_tackle_entry.player)
                # Don't use the move() function because it's not regular movement
                board.reset_position(diving_player.position)
                board.set_position(start_space, diving_player)
                board.set_prone(diving_player)
                yield DivingTackle(diving_player, start_space)

            if pickup_entry:
                result = pickup_entry.result
                if result == ActionResult.SUCCESS:
                    board.set_ball_carrier(player)
                yield Pickup(player, movement.position, result)
                if result != ActionResult.SUCCESS:
                    actions, new_result = self._process_action_reroll(cmds, log_entries, player, board,
                                                                      reroll_skill=Skills.SURE_HANDS)
                    yield from actions
                    if new_result:
                        result = new_result
                        if result == ActionResult.SUCCESS:
                            board.set_ball_carrier(player)
                        yield Pickup(player, movement.position, result)
                if result != ActionResult.SUCCESS:
                    failed_movement = True
                    find_turnover = True
                    for event in self._process_ball_movement(cmds, log_entries, board):
                        yield event
                        if isinstance(event, EndTurn):
                            find_turnover = False
                    if find_turnover:
                        log_entry = next(log_entries)
                        validate_log_entry(log_entry, TurnOverEntry, player.team.team_type)
                        yield from board.change_turn(player.team.team_type, log_entry.reason)
                    # Else we already found the turnover during the pickup
                pickup_entry = None

            start_space = target_space

        if turnover:
            log_entry = next(log_entries)
            validate_log_entry(log_entry, TurnOverEntry, player.team.team_type)
            yield from board.change_turn(player.team.team_type, log_entry.reason)

    def _process_pass(self, player, cmds, log_entries, board):
        throw_command = next(cmds)
        if board.get_ball_carrier() != player:
            raise ValueError(f"Got Pass command for {player} but ball carrier is {board.get_ball_carrier()}")

        log_entry = next(log_entries)
        if isinstance(log_entry, CatchEntry):
            # Interception
            intercepting_team = other_team(player.team.team_type)
            validate_log_entry(log_entry, CatchEntry, intercepting_team)
            intercepting_player = self.get_team(log_entry.team).get_player_by_number(log_entry.player)
            yield Interception(intercepting_player, log_entry.result, board)
            if log_entry.result == ActionResult.SUCCESS:
                board.set_ball_carrier(intercepting_player)
                turn_over_entry = next(log_entries)
                _ = next(cmds)  # Throw away the interception command
                yield EndTurn(player.team.team_type, player.number, turn_over_entry.reason, board)
                return
            else:
                throw_log_entry = next(log_entries)
        else:
            throw_log_entry = log_entry

        validate_log_entry(throw_log_entry, ThrowEntry, player.team.team_type, player.number)
        result = throw_log_entry.result
        yield Pass(player, throw_command.position, result, board)
        _ = next(cmds)  # Throw away the interception command, which we seem to get even if it's not possible

        if throw_log_entry.result != ThrowResult.ACCURATE_PASS and player.team == board.turn_team:
            actions, result = self._process_action_reroll(cmds, log_entries, player, board, reroll_skill=Skills.PASS)
            yield from actions
            yield Pass(player, throw_command.position, result, board)

        if result == ThrowResult.FUMBLE:
            scatter_entry = next(log_entries)
            start_position = board.get_ball_position()
            ball_position = scatter(start_position, scatter_entry.direction)
            board.set_ball_position(ball_position)
            yield Bounce(start_position, ball_position, scatter_entry.direction, board)
        elif result == ThrowResult.ACCURATE_PASS:
            ball_position = throw_command.position
            board.set_ball_position(ball_position)
        else:
            scatter_1 = next(log_entries)
            scatter_2 = next(log_entries)
            scatter_3 = next(log_entries)
            ball_position = scatter(throw_command.position, scatter_1.direction)
            ball_position = scatter(ball_position, scatter_2.direction)
            ball_position = scatter(ball_position, scatter_3.direction)
            board.set_ball_position(ball_position)
            yield Scatter(throw_command.position, ball_position, board)
        yield from self._process_catch(ball_position, cmds, log_entries, board,
                                       bounce_on_empty=result != ThrowResult.FUMBLE)

    def _process_catch(self, ball_position, cmds, log_entries, board, bounce_on_empty=False):
        catcher = board.get_position(ball_position)
        caught = False
        if catcher and not board.is_prone(catcher):
            catch_entry = next(log_entries)
            for event in self._process_action_result(catch_entry, CatchEntry, cmds, log_entries, catcher,
                                                     ActionType.CATCH, board, is_active=False):
                if isinstance(event, Action) and event.action == ActionType.CATCH \
                        and event.result == ActionResult.SUCCESS:
                    board.set_ball_carrier(catcher)
                    caught = True
                yield event
        if not caught or (not catcher and bounce_on_empty):
            yield from self._process_ball_movement(cmds, log_entries, board)

    def _process_ball_movement(self, cmds, log_entries, board):
        if isinstance(log_entries.peek(), ThrowInDirectionLogEntry):
            yield from self._process_throwin(cmds, log_entries, board)
            return

        log_entry = next(log_entries)
        if not isinstance(log_entry, BounceLogEntry):
            raise ValueError(f"Expected BounceLogEntry but got {type(log_entry).__name__}")
        old_ball_position = board.get_ball_position()
        ball_position = scatter(old_ball_position, log_entry.direction)
        board.set_ball_position(ball_position)
        bounce_event = Bounce(old_ball_position, ball_position, log_entry.direction, board)
        if ball_position.is_offpitch():
            yield bounce_event
            if ball_position.x < 0 or ball_position.x >= PITCH_WIDTH:
                offset = 0
                # Throw-ins from fumbled pickups seem to come from the space where the ball
                # would have landed if there was an off-board space rather than the one adjacent
                # to where the pickup was attempted
                if log_entry.direction in _norths:
                    offset = 1
                elif log_entry.direction in _souths:
                    offset = -1
                board.set_ball_position(old_ball_position.add(0, offset))
            yield from self._process_throwin(cmds, log_entries, board)
        elif board.get_position(ball_position):
            # Bounced to an occupied space, so we need to continue for a catch or a bounce off a prone body
            player_in_space = board.get_position(ball_position)
            if board.is_prone(player_in_space):
                yield bounce_event
                yield from self._process_ball_movement(cmds, log_entries, board)
            else:
                log_entry = log_entries.peek()
                if isinstance(log_entry, CatchEntry):
                    yield bounce_event
                    yield from self._process_catch(ball_position, cmds, log_entries, board)
                elif isinstance(log_entry, BounceLogEntry):
                    # The first bounce was a ghost bounce that never happened, so ignore it
                    board.set_ball_position(old_ball_position)
                    yield from self._process_ball_movement(cmds, log_entries, board)
                else:
                    raise ValueError("Expected CatchEntry or BounceEntry after bounce, "
                                     f"got {type(log_entry).__name__}")
        else:
            # Bounced to an empty space
            # But sometimes it gets a ghost bounce
            if isinstance(log_entries.peek(), BounceLogEntry):
                log_entry = next(log_entries)
                ball_position = scatter(old_ball_position, log_entry.direction)
                board.set_ball_position(ball_position)
                bounce_event = Bounce(old_ball_position, ball_position, log_entry.direction, board)
            yield bounce_event

    def _process_throwin(self, cmds, log_entries, board):
        log_entry = next(log_entries)
        if not isinstance(log_entry, ThrowInDirectionLogEntry):
            raise ValueError(f"Expected ThrowInDirection log entry but got {type(log_entry).__name__}")
        distance_entry = next(log_entries)
        previous_ball_position = board.get_ball_position()
        ball_position = throwin(previous_ball_position, board.get_play_direction(),
                                log_entry.direction, distance_entry.distance)
        board.set_ball_position(ball_position)
        yield ThrowIn(previous_ball_position, ball_position, log_entry.direction, distance_entry.distance,
                      board)
        yield from self._process_ball_movement(cmds, log_entries, board)

    def _process_spell(self, cmds, log_entries, board):
        # Fireball and lightning may not be too different, as there's just a different number of targets
        # with a different roll, and we don't care about the roll value
        cmd = next(cmds)
        if not isinstance(cmd, SpellCommand):
            raise ValueError(f"Expected SpellCommand for spell but got {type(cmd).__name__}")
        # Don't take the log entry so that the loop is consistent
        log_entry = log_entries.peek()
        if not isinstance(log_entry, SpellEntry):
            raise ValueError(f"Expected SpellEntry but got {type(log_entry).__name__}")
        target = cmd.position
        yield Spell(target, log_entry.spell_type, board)
        bounces = []
        while True:
            log_entry = log_entries.peek()
            if isinstance(log_entry, BounceLogEntry):
                log_entry = next(log_entries)
                bounces.append(log_entry)
            elif isinstance(log_entry, SpellEntry):
                log_entry = next(log_entries)
                player = self.get_team(log_entry.team).get_player_by_number(log_entry.player)
                yield Action(player, ActionType.SPELL_HIT, log_entry.result, board)
                if log_entry.result == ActionResult.SUCCESS:
                    log_entry = next(log_entries)
                    yield from self._process_armour_roll(player, cmds, log_entry, log_entries, board)
            else:
                break

        if bounces:
            yield from self._process_ball_movement(cmds, self.__generator(bounces), board)


def find_next_known_command(generator):
    cur = next(generator)
    while type(cur) == Command:
        cur = next(generator)
    return cur


def is_dodge(board, player, destination):
    if board.quick_snap_turn:
        return False
    elif player.position == destination:
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
    pushbacks = [coord for coord in possible_coords if on_pitch(coord) and not board.get_position(coord)]
    if not pushbacks and any(not on_pitch(coord) for coord in possible_coords):
        pushbacks = [OFF_PITCH_POSITION]
    return pushbacks


def on_pitch(coord):
    return coord.x >= 0 and coord.x <= LAST_COLUMN_IDX and coord.y >= 0 and coord.y <= FAR_ENDZONE_IDX


def calculate_pushback(blocker_coords, old_coords, board):
    return calculate_pushbacks(blocker_coords, old_coords, board)[0]
