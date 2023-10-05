from typing import Optional

import dataclasses
import enum


class Attribute(str, enum.Enum):
  PHYSICAL = 'physical'
  MENTAL = 'mental'
  EMOTIONAL = 'emotional'


class Difficulty(str, enum.Enum):
  pass


@dataclasses.dataclass(frozen=True)
class Character:
  name: str
  title: str
  description: str
  strength: Attribute | None = None
  weakness: Attribute | None = None

@dataclasses.dataclass(frozen=True)
class Outcome:
  description: str
  quest: Optional['Quest']


@dataclasses.dataclass(frozen=True)
class Action:
  description: str
  difficulty: Difficulty
  attribute: Attribute | None
  success: Outcome
  failure: Outcome


@dataclasses.dataclass(frozen=True)
class Quest:
  name: str
  description: str
  success_brief: str
  failure_brief: str
  actions: list[Action] | None = None



@dataclasses.dataclass(frozen=True)
class Location:
  name: str
  description: str
  quest: Quest | None = None


@dataclasses.dataclass(frozen=True)
class Overview:
  name: str | None = None
  description: str | None = None

