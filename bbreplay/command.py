# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from enum import Enum
from .teams import player_idx_to_type, PlayerType


class CoinToss(Enum):
    HEADS = 1
    TAILS = 0


class Role(Enum):
    KICK = 0
    RECEIVE = 1

class Command:
    def __init__(self, id, turn, team, command_type, data):
        self.id = id
        self.turn = turn
        self.team = team
        self.command_type = command_type
        self._data = data

    def __repr__(self):
        return f'UnknownCommand(id={self.id}, turn={self.turn}, team={self.team},' \
            f' cmd_type={self.command_type}, data={self._data})'


class SimpleCommand(Command):
    def __init__(self, name, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.name = name
        # Data is always 0s
    
    def __repr__(self):
        # Note: This isn't always useful in Hotseat games where the player ID is always 1.8e19 (8-byte unsigned max)
        return f'{self.name}(team={self.team}, data={self._data})'


class SimpleTeamOverrideCommand(SimpleCommand):
    def __init__(self, name, id, turn, team, command_type, data):
        super().__init__(name, id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0]) # Override the team


class SetupCommand(Command):
    # TODO: AI setup doesn't show up
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0]) # Override the team
        self.player_idx = data[1]
        self.x = data[2]
        self.y = data[3]

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
        self.team = player_idx_to_type(data[0]) # Override the team
        self.player_idx = data[1]
        self.sequence = data[2]
        self.action_type = data[4]
        self.x = data[8]
        self.y = data[9]
    
    def __repr__(self):
        return f'UnknownPlayerCommand(team={self.team}, player={self.player_idx}, sequence={self.sequence}, ' \
            f'action_type={self.action_type}, target={self.x},{self.y}, data={self._data})'


class MovementCommand(PlayerCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)

    def __repr__(self):
        return f'Movement(team={self.team}, player={self.player_idx}, sequence={self.sequence}, move_to={self.x},{self.y}, ' \
            f'data={self._data})'


class BlockCommand(PlayerCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
    
    def __repr__(self):
        return f'BlockCommand(team={self.team}, player={self.player_idx}, sequence={self.sequence}, target={self.x},{self.y}, ' \
            f'data={self._data})'


class KickoffCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.x = data[0]
        self.y = data[1]
    
    def __repr__(self):
        return f'Kickoff(team={self.team}, pos={self.x},{self.y}, data={self._data})'


class PreKickoffCompleteCommand(SimpleTeamOverrideCommand):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__('PreKickoffComplete', id, turn, team, command_type, data)


class BlockDiceChoiceCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0]) # Override the team
        self.player_idx = data[1]
        self.dice_idx = data[2]
    
    def __repr__(self):
        return f'BlockDiceChoice(team={self.team}, player={self.player_idx}, dice_idx={self.dice_idx}, data={self._data})'


class PickupBallCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)


class PushbackCommand(Command):
    def __init__(self, id, turn, team, command_type, data):
        super().__init__(id, turn, team, command_type, data)
        self.team = player_idx_to_type(data[0]) # Override the team
        self.player_idx = data[1]
        self.x = data[2]
        self.y = data[3]
    
    def __repr__(self):
        return f'Pushback(team={self.team}, pushing_player={self.player_idx}, push_destination={self.x},{self.y}, data={self._data})'


class NetworkCommand(SimpleCommand):
    # These commands are only seen in online games and never in local exhibitions
    def __init__(self, id, turn, team, command_type, data):
        super().__init__("Network", id, turn, team, command_type, data)


def create_player_command(id, turn, team, command_type, data):
    action_type = data[4]

    if action_type == 25:
        return MovementCommand(id, turn, team, command_type, data)
    elif action_type == 26:
        return BlockCommand(id, turn, team, command_type, data)
    else:
        return PlayerCommand(id, turn, team, command_type, data)
    

MOVE_MAP = {
    6: CoinTossCommand,
    7: RoleCommand,
    8: SetupCommand,
    9: SetupCompleteCommand,
    10: KickoffCommand,
    14: PreKickoffCompleteCommand,
    17: EndTurnCommand,
    19: BlockDiceChoiceCommand,
    25: create_player_command,
    26: PickupBallCommand,
    46: PushbackCommand,
    59: AbandonMatchCommand,
    69: NetworkCommand,
    94: NetworkCommand
}


def create_command(replay, row):
    command_id, turn, player_idx, command_type, *data = row
    team = player_idx_to_type(player_idx - 1)
    command = MOVE_MAP.get(command_type, Command)
    return command(command_id, turn, team, command_type, data)
