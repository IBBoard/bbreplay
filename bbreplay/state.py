# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from collections import defaultdict
from . import BEFORE_HALFWAY_IDX, FAR_ENDZONE_IDX, NEAR_ENDZONE_IDX, PlayDirection, other_team, Skills, TeamType, \
    ActionResult, PITCH_LENGTH, PITCH_WIDTH, OFF_PITCH_POSITION, Weather


HALF_TIME_TURN = 8


class GameState:
    def __init__(self, home_team, away_team, receiving_team):
        self.teams = [home_team, away_team]
        self.__first_receiving_team = receiving_team
        self.__receiving_team = receiving_team
        self.score = [0, 0]
        self.turn_team = None
        self.__rerolls = [home_team.rerolls, away_team.rerolls]
        self.apothecaries = [home_team.apothecaries, away_team.apothecaries]
        self.__reset_board()
        self.__turn = 0
        self.__prone = set()
        self.__injured = set()
        self.__stupid = set()
        self.__tested_stupid = set()
        self.__wild_animal = set()
        self.__tested_wild_animal = set()
        self.__ball_position = OFF_PITCH_POSITION
        self.__ball_carrier = None
        self.weather = None
        self.kickoff_event = None
        self.quick_snap_turn = False
        self.__setups = [[], []]
        self.__last_setup_turn = 0
        self.__moves = defaultdict(int)
        self.__used_reroll = False
        self.__leader_reroll = [False, False]
        self.__used_leaders = set()
        self.__touchdown_row = [-1, -1]

    @property
    def turn(self):
        return self.__turn // 2 + 1

    def set_weather(self, weather):
        self.weather = weather if not self.weather or weather != Weather.NICE else Weather.NICE_BOUNCY

    def blitz(self):
        self.__turn -= 1
        self.turn_team = self.teams[other_team(self.receiving_team).value]

    def quick_snap(self):
        self.__turn -= 1
        self.quick_snap_turn = True

    def halftime(self):
        self.__receiving_team = other_team(self.__first_receiving_team)

    @property
    def receiving_team(self):
        return self.__receiving_team

    @property
    def kicking_team(self):
        return other_team(self.__receiving_team)

    @property
    def rerolls(self):
        home_rerolls, away_rerolls = self.__rerolls
        if self.has_leader_reroll(TeamType.HOME):
            home_rerolls += 1
        if self.has_leader_reroll(TeamType.AWAY):
            away_rerolls += 1
        return (home_rerolls, away_rerolls)

    def prepare_setup(self):
        crossed_half_time = (self.turn <= HALF_TIME_TURN) != (self.__last_setup_turn <= HALF_TIME_TURN)
        self.__reset_board()
        self.__prone.clear()
        self.__stupid.clear()
        self.__wild_animal.clear()
        for team_setup in self.__setups:
            deployed_subs = set()
            subs = (player for player, position in team_setup if position.is_offpitch())
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

        if crossed_half_time:
            self.__used_leaders.clear()
            self.__rerolls = [team.rerolls for team in self.teams]

        self.set_ball_position(OFF_PITCH_POSITION)

    def setup_complete(self):
        for team in self.teams:
            team_setup = []
            for player in team.get_players():
                team_setup.append((player, player.position))
            self.__setups[team.team_type.value] = team_setup
        self.turn_team = self.teams[self.__receiving_team.value]

        if any(player.is_on_pitch() and Skills.LEADER in player.skills
               and player not in self.__used_leaders
               for player in self.teams[TeamType.HOME.value].get_players()):
            self.__leader_reroll[TeamType.HOME.value] = True
        else:
            self.__leader_reroll[TeamType.HOME.value] = False

        if any(player.is_on_pitch() and Skills.LEADER in player.skills
               and player not in self.__used_leaders
               for player in self.teams[TeamType.AWAY.value].get_players()):
            self.__leader_reroll[TeamType.AWAY.value] = True
        else:
            self.__leader_reroll[TeamType.AWAY.value] = False

        if any(pos.y > BEFORE_HALFWAY_IDX for _, pos in self.__setups[TeamType.HOME.value]):
            self.__touchdown_row = [NEAR_ENDZONE_IDX, FAR_ENDZONE_IDX]
        else:
            self.__touchdown_row = [FAR_ENDZONE_IDX, NEAR_ENDZONE_IDX]
        self.__last_setup_turn = self.turn

    def get_play_direction(self):
        return PlayDirection.DOWN_PITCH if self.__touchdown_row[self.__receiving_team.value] == FAR_ENDZONE_IDX \
            else PlayDirection.UP_PITCH

    def is_touchdown_state(self):
        ball_carrier = self.get_ball_carrier()
        return ball_carrier and ball_carrier.position.y == self.__touchdown_row[ball_carrier.team.team_type.value]

    def touchdown(self, player):
        team = player.team.team_type
        team_value = team.value
        self.score[team_value] += 1
        self.__receiving_team = other_team(team)

    def kickoff(self):
        self.turn_team = self.teams[self.__receiving_team.value]

    def start_turn(self, team):
        if team != self.turn_team.team_type and team != TeamType.HOTSEAT:
            raise ValueError(f'Out of order start turn - expected {self.turn_team.team_type} but got {team}')
        self.__tested_stupid.clear()
        self.__tested_wild_animal.clear()
        self.__wild_animal.clear()
        self.__moves.clear()
        self.__used_reroll = False

    def end_turn(self, team):
        if team != self.turn_team.team_type and team != TeamType.HOTSEAT:
            raise ValueError(f'Out of order end turn - expected {self.turn_team.team_type} but got {team}')
        self.__turn += 1
        self.quick_snap_turn = False
        next_team = other_team(team)
        self.turn_team = self.teams[next_team.value]

    def roll_back_turn(self):
        self.__turn -= 2

    def move(self, player, from_space, to_space):
        self.__moves[player] += max(abs(from_space.x - to_space.x), abs(from_space.y - to_space.y))
        self.reset_position(from_space)
        self.set_position(to_space, player)

    def throw_block(self, player):
        self.__moves[player] += 1

    def get_distance_moved(self, player):
        return self.__moves[player]

    def set_position(self, position, contents):
        if not position.is_offpitch():
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

    def unset_prone(self, player, penalise_movement=True):
        self.__prone.remove(player)
        if penalise_movement:
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

    def __do_test(self, player, result, tested_players, failed_players):
        tested_players.add(player)
        if result != ActionResult.SUCCESS:
            failed_players.add(player)
        elif self.is_stupid(player):
            failed_players.remove(player)

    def stupidity_test(self, player, result):
        self.__do_test(player, result, self.__tested_stupid, self.__stupid)

    def tested_stupid(self, player):
        return player in self.__tested_stupid

    def wild_animal_test(self, player, result):
        self.__do_test(player, result, self.__tested_wild_animal, self.__wild_animal)

    def is_wild_animal(self, player):
        return player in self.__wild_animal

    def tested_wild_animal(self, player):
        return player in self.__tested_wild_animal

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
        if self.__leader_reroll[team.value]:
            raise ValueError("Attempted to use a normal reroll when a leader reroll exists")
        self.__rerolls[team.value] -= 1
        self.__used_reroll = True

    def use_leader_reroll(self, team, player):
        self.__used_leaders.add(player)
        self.__leader_reroll[team.value] = False
        self.__used_reroll = True

    def can_reroll(self, team):
        return self.rerolls[team.value] > 0 and not self.__used_reroll

    def add_reroll(self, team):
        self.__rerolls[team.value] += 1

    def has_leader_reroll(self, team):
        return self.__leader_reroll[team.value]

    def has_apothecary(self, team):
        return self.apothecaries[team.value] > 0

    def use_apothecary(self, team):
        self.apothecaries[team.value] -= 1

    def __reset_board(self):
        self.__board = [[None] * PITCH_WIDTH for _ in range(PITCH_LENGTH)]
        for team in self.teams:
            for player in team.get_players():
                player.position = OFF_PITCH_POSITION
