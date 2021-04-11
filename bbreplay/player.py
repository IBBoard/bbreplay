# Copyright © 2021, IBBoard
# Licensed under GPLv3 or later - see COPYING

from . import prefix_for_teamtype, PlayerStatus, Skills, OFF_PITCH_POSITION


class Positionable:
    def __init__(self):
        self.position = OFF_PITCH_POSITION

    def is_on_pitch(self):
        return self.position != OFF_PITCH_POSITION


class Ball(Positionable):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return f"Ball({self.position})"


class Player(Positionable):
    def __init__(self, team, db_id, number, name, move, strength, agility, armour_value, level, spp, value, db):
        super().__init__()
        self.__dbid = db_id
        self.team = team
        self.number = number
        self.name = name
        # TODO: Convert stats
        self.MA = move
        self.ST = strength
        self.AG = agility
        self.AV = armour_value
        self.level = level
        self.SPP = spp
        self.value = value
        self.status = PlayerStatus.OKAY
        self.__db = db
        self.__skills = None

    @property
    def skills(self):
        if self.__skills is None:
            self.__skills = []
            table_prefix = prefix_for_teamtype(self.team.team_type)
            cur = self.__db.cursor()
            type_skills = cur.execute(f'SELECT idSkill_Listing, description FROM {table_prefix}_Player_Listing player '
                                      f'INNER JOIN {table_prefix}_Player_Type_Skills type_skills '
                                      'ON player.idPlayer_Types = type_skills.idPlayer_Types '
                                      f'WHERE player.ID = {self.__dbid} ')

            for skill_row in type_skills:
                try:
                    self.__skills.append(Skills(skill_row[0]))
                except ValueError as ex:
                    raise ValueError(f"Unidentified skill {skill_row[0]} ({skill_row[1]}) for {self.team.name} player "
                                     f"#{self.number} {self.name}") from ex

            learned_skills = cur.execute(f'SELECT idSkill_Listing FROM {table_prefix}_Player_Skills '
                                         f'WHERE idPlayer_Listing = {self.__dbid}')

            for skill_row in learned_skills:
                try:
                    self.__skills.append(Skills(skill_row[0]))
                except ValueError as ex:
                    raise ValueError(f"Unidentified learned skill {skill_row[0]} for {self.team.name} player "
                                     f"#{self.number} {self.name}") from ex
            cur.close()
        return self.__skills

    def __repr__(self):
        return f"Player(number={self.number}, name={self.name}, " \
               f"level={self.level}, spp={self.SPP}, value={self.value}, {self.position})"
