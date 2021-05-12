# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from collections import namedtuple, defaultdict
from . import other_team, Skills, TeamType, Weather, ActionResult, PITCH_LENGTH, PITCH_WIDTH, OFF_PITCH_POSITION


WeatherTuple = namedtuple('Weather', ['result'])
EndTurn = namedtuple('EndTurn', ['team', 'number', 'reason', 'board'])
StartTurn = namedtuple('StartTurn', ['team', 'number', 'board'])
HalfTime = namedtuple('HalfTime', ['board'])
AbandonMatch = namedtuple('AbandonMatch', ['team', 'board'])
EndMatch = namedtuple('EndMatch', ['board'])

HALF_TIME_TURN = 8


class GameState:
    def __init__(self, home_team, away_team, receiving_team):
        self.teams = [home_team, away_team]
        self.__receiving_team = receiving_team
        self.score = [0, 0]
        self.turn_team = None
        self.rerolls = [home_team.rerolls, away_team.rerolls]
        self.__reset_board()
        self.__turn = 0
        self.__prone = set()
        self.__injured = set()
        self.__stupid = set()
        self.__tested_stupid = set()
        self.__ball_position = OFF_PITCH_POSITION
        self.__ball_carrier = None
        self.__double_nice_weather = False
        self.weather = None
        self.__setups = [[], []]
        self.__last_setup_turn = 0
        self.__moves = defaultdict(int)
        self.__used_reroll = False

    @property
    def turn(self):
        return self.__turn // 2 + 1

    def set_weather(self, weather):
        self.weather = weather if not self.weather or weather != Weather.NICE else Weather.NICE_BOUNCY
        return WeatherTuple(self.weather)

    def blitz(self):
        self.__turn -= 1

    def halftime(self):
        self.__receiving_team = other_team(self.__receiving_team)
        return HalfTime(self)

    @property
    def receiving_team(self):
        return self.__receiving_team

    @property
    def kicking_team(self):
        return other_team(self.__receiving_team)

    def prepare_setup(self):
        crossed_half_time = (self.turn <= HALF_TIME_TURN) != (self.__last_setup_turn <= HALF_TIME_TURN)
        self.__reset_board()
        self.__prone.clear()
        self.__stupid.clear()
        for team_setup in self.__setups:
            deployed_subs = set()
            subs = (player for player, position in team_setup if position == OFF_PITCH_POSITION)
            for player, position in team_setup:
                if player in deployed_subs:
                    continue
                position = position if not crossed_half_time else position.invert()
                if not self.is_injured(player):
                    self.set_position(position, player)
                else:
                    replacement_player = next(subs, None)
                    self.set_position(position, replacement_player)
                    deployed_subs.add(replacement_player)

        self.set_ball_position(OFF_PITCH_POSITION)

    def setup_complete(self):
        for team in self.teams:
            team_setup = []
            for player in team.get_players():
                team_setup.append((player, player.position))
            self.__setups[team.team_type.value] = team_setup

    def touchdown(self, player):
        team = player.team.team_type
        team_value = team.value
        self.score[team_value] += 1
        self.__receiving_team = other_team(team)

    def kickoff(self):
        self.turn_team = self.teams[self.__receiving_team.value]
        self.rerolls = [team.rerolls for team in self.teams]
        if any(player.is_on_pitch() and Skills.LEADER in player.skills
               for player in self.teams[TeamType.HOME.value].get_players()):
            self.add_reroll(TeamType.HOME)
        if any(player.is_on_pitch() and Skills.LEADER in player.skills
               for player in self.teams[TeamType.AWAY.value].get_players()):
            self.add_reroll(TeamType.AWAY)
        self.__last_setup_turn = self.turn
        yield from self.start_turn(self.__receiving_team)

    def change_turn(self, ending_team, reason):
        yield from self.end_turn(ending_team, reason)
        yield from self.start_turn(other_team(ending_team))

    def start_turn(self, team):
        if team != self.turn_team.team_type and team != TeamType.HOTSEAT:
            raise ValueError(f'Out of order start turn - expected {self.turn_team.team_type} but got {team}')
        self.__tested_stupid.clear()
        self.__moves.clear()
        self.__used_reroll = False
        yield StartTurn(team, self.turn, self)

    def end_turn(self, team, reason):
        if team != self.turn_team.team_type and team != TeamType.HOTSEAT:
            raise ValueError(f'Out of order end turn - expected {self.turn_team.team_type} but got {team}')
        yield EndTurn(self.turn_team.team_type, self.turn, reason, self)
        self.__turn += 1
        if self.__turn == 32:
            yield EndMatch(self)
            return
        next_team = other_team(team)
        self.turn_team = self.teams[next_team.value]

    def abandon_match(self, team):
        if team != self.turn_team.team_type and team != TeamType.HOTSEAT:
            raise ValueError(f'Out of order match abandonment - expected {self.turn_team.team_type} but got {team}')
        yield EndTurn(team, self.turn, 'Abandon match', self)
        yield AbandonMatch(team, self)

    def move(self, player, from_space, to_space):
        self.__moves[player] += max(abs(from_space.x - to_space.x), abs(from_space.y - to_space.y))
        self.reset_position(from_space)
        self.set_position(to_space, player)

    def get_distance_moved(self, player):
        return self.__moves[player]

    def set_position(self, position, contents):
        if position != OFF_PITCH_POSITION:
            self.__board[position.y][position.x] = contents
        if contents:
            contents.position = position

    def reset_position(self, position):
        self.set_position(position, None)

    def get_position(self, position):
        return self.__board[position.y][position.x]

    def set_ball_position(self, position):
        self.__ball_carrier = None
        self.__ball_position = position

    def set_ball_carrier(self, player):
        if not player and self.__ball_carrier:
            self.__ball_position = self.__ball_carrier.position
        self.__ball_carrier = player

    def get_ball_position(self):
        if self.__ball_carrier:
            return self.__ball_carrier.position
        else:
            return self.__ball_position

    def get_ball_carrier(self):
        return self.__ball_carrier

    def __getitem__(self, idx):
        return self.__board[idx]

    def has_tacklezone(self, player):
        return not self.is_prone(player) and player not in self.__stupid

    def set_prone(self, player):
        self.__prone.add(player)

    def unset_prone(self, player):
        self.__prone.remove(player)
        self.__moves[player] += 3

    def is_prone(self, player):
        return player in self.__prone

    def set_injured(self, player):
        self.__injured.add(player)

    def unset_injured(self, player):
        self.__injured.remove(player)

    def is_injured(self, player):
        return player in self.__injured

    def is_stupid(self, player):
        return player in self.__stupid

    def stupidity_test(self, player, result):
        self.__tested_stupid.add(player)
        if result != ActionResult.SUCCESS:
            self.__stupid.add(player)
        elif self.is_stupid(player):
            self.__stupid.remove(player)

    def tested_stupid(self, player):
        return player in self.__tested_stupid

    def get_surrounding_players(self, position):
        entities = []
        for i in [-1, 0, 1]:
            x = position.x + i
            if x < 0 or x >= PITCH_WIDTH:
                continue
            for j in [-1, 0, 1]:
                y = position.y + j
                if y < 0 or y >= PITCH_LENGTH:
                    continue
                if i == 0 and j == 0:
                    continue
                entity = self.__board[y][x]
                if entity:
                    entities.append(entity)
        return entities

    def use_reroll(self, team):
        if self.__used_reroll:
            raise ValueError("Already used a team reroll this turn!")
        self.rerolls[team.value] -= 1
        self.__used_reroll = True

    def can_reroll(self, team):
        return self.rerolls[team.value] > 0 and not self.__used_reroll

    def add_reroll(self, team):
        self.rerolls[team.value] += 1

    def __reset_board(self):
        self.__board = [[None] * PITCH_WIDTH for _ in range(PITCH_LENGTH)]
        for team in self.teams:
            for player in team.get_players():
                player.position = OFF_PITCH_POSITION
