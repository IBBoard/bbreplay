# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from . import player_idx_to_type
from . import CoinToss, Role, Position, CasualtyResult


class Command:
    def __init__(self, id, turn, team, command_type, data, is_verbose=False):
        self.id = id
        self.turn = turn
        self.team = team
        self.command_type = command_type
        self._data = data
        self.is_verbose = is_verbose

    def __repr__(self):
        return f'UnknownCommand(id={self.id}, turn={self.turn}, team={self.team},' \
            f' cmd_type={self.command_type}, data={self._data})'


class SimpleCommand(Command):
    def __init__(self, name, id, turn, team, command_type, data, is_verbose=False):
        super().__init__(id, turn, team, command_type, data, is_verbose)
        self.name = name
        # Data is always 0s

    def __repr__(self):
        # Note: This isn't always useful in Hotseat games where the player ID is always 1.8e19 (8-byte unsigned max)
        return f'{self.name}(team={self.team}, data={self._data})'


class SimpleTeamOverrideCommand(SimpleCommand):
    def __init__(self, name, id, turn, team, command_type, data):
        super().__init__(name, id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0])  # Override the team


class SetupCommand(Command):
    # TODO: AI setup doesn't show up
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0])  # Override the team
        self.player_idx = data[1]
        self.position = Position(data[2], data[3])

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    def __repr__(self):
        return f'Setup(team={self.team}, player={self.player_idx}, pos={self.x},{self.y}, data={self._data})'


class SetupCompleteCommand(SimpleCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__("SetupComplete", id, turn, team, command_type, data)


class AbandonMatchCommand(SimpleCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__("AbandonMatch", id, turn, team, command_type, data)


class EndTurnCommand(SimpleTeamOverrideCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__('EndTurn', id, turn, team, command_type, data)


class CoinTossCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.choice = CoinToss(data[0])

    def __repr__(self):
        return f'CoinToss(team={self.team}, choice={self.choice}, data={self._data})'


class RoleCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.choice = Role(data[0])

    def __repr__(self):
        return f'Role(team={self.team}, choice={self.choice}, data={self._data})'


class PlayerCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0])  # Override the team
        self.player_idx = data[1]
        self.sequence = data[2]
        self.action_type = data[4]
        self.position = Position(data[8], data[9])

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    def __repr__(self):
        return f'UnknownPlayerCommand(team={self.team}, player={self.player_idx}, sequence={self.sequence}, ' \
            f'action_type={self.action_type}, target={self.x},{self.y}, data={self._data})'


class MovementCommand(PlayerCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)

    def __repr__(self):
        return f'Movement(team={self.team}, player={self.player_idx}, sequence={self.sequence}, ' \
            f'move_to={self.x},{self.y}, data={self._data})'


class EndMovementCommand(MovementCommand):
    # Note: This may just end a sequence of moves, not the player's entire turn
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)

    def __repr__(self):
        return f'EndMovement(team={self.team}, player={self.player_idx}, sequence={self.sequence}, ' \
            f'move_to={self.x},{self.y}, data={self._data})'


class TargetSpaceCommand(PlayerCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)

    def __repr__(self):
        return f'Block(team={self.team}, player={self.player_idx}, sequence={self.sequence}, ' \
            f'target={self.x},{self.y}, data={self._data})'


class KickoffCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.position = Position(data[0], data[1])

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    def __repr__(self):
        return f'Kickoff(team={self.team}, pos={self.x},{self.y}, data={self._data})'


class PreKickoffCompleteCommand(SimpleTeamOverrideCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__('PreKickoffComplete', id, turn, team, command_type, data)


class DiceChoiceCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0])  # Override the team
        self.player_idx = data[1]
        self.dice_idx = data[2]

    def __repr__(self):
        return f'DiceChoice(team={self.team}, player={self.player_idx}, dice_idx={self.dice_idx}, ' \
            f'data={self._data})'


class TargetPlayerCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0])  # Override the team
        self.player_idx = data[1]
        self.target_team = player_idx_to_type(data[2])
        self.target_player = data[3]
        # data[4] and data[5] are 255 and 255 *or* below ~20
        # data[8] is often 0 but sometimes 1

    def __repr__(self):
        return f'TargetPlayerCommand(team={self.team}, player={self.player_idx}, ' \
               f'target_team={self.target_team}, target_player={self.target_player}, data={self._data})'


class FollowUpChoiceCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.choice = data[0] == 1

    def __repr__(self):
        return f'FollowUp(team={self.team}, choice={self.choice}, data={self._data})'


class PushbackCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0])  # Override the team
        self.player_idx = data[1]
        self.position = Position(data[2], data[3])

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    def __repr__(self):
        return f'Pushback(team={self.team}, pushing_player={self.player_idx}, push_destination={self.x},{self.y}, ' \
            f'data={self._data})'


class DumpOffCommand(SimpleCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__("DumpOff", id, turn, team, command_type, data)


class ThrowCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0])  # Override the team
        self.player_idx = data[1]
        self.position = Position(data[2], data[3])

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    def __repr__(self):
        return f'Throw(team={self.team}, player={self.player_idx}, position={self.x},{self.y})'


class RerollCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        # 0 and 1 MIGHT be team and player IDX, but it doesn't always match
        super().__init__(id, turn, team, command_type, data)

    def __repr__(self):
        return f'Reroll(team={self.team}, data={self._data})'


class ProRerollCommand(SimpleTeamOverrideCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__('ProReroll', id, turn, team, command_type, data)
        self.player = data[1]

    def __repr__(self):
        return f'ProReroll(team={self.team}, player={self.player}, data={self._data})'


class DeclineRerollCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        # Only ever seen data of [1,0,0,0,0,0,0,0] and TeamType.HOME in online matches or HOTSEAT in local exhibitions
        super().__init__(id, turn, team, command_type, data)

    def __repr__(self):
        return f'DeclineReroll(data={self._data})'


class ApothecaryCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.player = data[1]
        self.used = data[2] == 1

    def __repr__(self):
        return f'Apothecary(team={self.team}, player={self.player}, used={self.used}, data={self._data})'


class ApothecaryChoiceCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.player = data[1]
        self.result = CasualtyResult(data[2])

    def __repr__(self):
        return f'ApothecaryChoice(team={self.team}, player={self.player}, result={self.result}, data={self._data})'


class NetworkCommand(SimpleCommand):
    # These commands are only seen in online games and never in local exhibitions
    def __init__(self, id, turn, team, command_type, data):
        super().__init__("Network", id, turn, team, command_type, data, True)


class UnknownVerboseCommand(SimpleCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(f"UnknownVerboseCommand{command_type}", id, turn, team, command_type, data, True)


def create_player_command(id, turn, team, command_type, data):
    action_type = data[4]

    if action_type == 25:
        return MovementCommand(id, turn, team, command_type, data)
    elif action_type == 26:
        return TargetSpaceCommand(id, turn, team, command_type, data)
    elif action_type == 24:
        return EndMovementCommand(id, turn, team, command_type, data)
    else:
        return PlayerCommand(id, turn, team, command_type, data)


MOVE_MAP = {
    6: CoinTossCommand,
    7: RoleCommand,
    8: SetupCommand,
    9: SetupCompleteCommand,
    10: KickoffCommand,
    # 13: Intercept?
    14: PreKickoffCompleteCommand,
    17: EndTurnCommand,
    19: DiceChoiceCommand,
    20: RerollCommand,
    21: ProRerollCommand,
    23: ApothecaryChoiceCommand,
    25: create_player_command,
    26: TargetPlayerCommand,
    29: ApothecaryCommand,
    30: ThrowCommand,
    33: UnknownVerboseCommand,
    45: FollowUpChoiceCommand,
    46: PushbackCommand,
    49: DumpOffCommand,
    51: DeclineRerollCommand,
    59: AbandonMatchCommand,
    69: NetworkCommand,
    # Block related? After DiceChoice and before PushbackCommand
    91: UnknownVerboseCommand,
    # Block related? After DiceChoice and before PushbackCommand
    92: UnknownVerboseCommand,
    94: NetworkCommand
}


def create_command(replay, row):
    command_id, turn, player_idx, command_type, *data = row
    team = player_idx_to_type(player_idx - 1)
    command = MOVE_MAP.get(command_type, Command)
    return command(command_id, turn, team, command_type, data)
