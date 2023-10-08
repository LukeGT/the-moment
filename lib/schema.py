from typing import Optional

import dataclasses
import enum
import pydantic
import textwrap


class Attribute(str, enum.Enum):
  PHYSICAL = 'physical'
  MENTAL = 'mental'
  EMOTIONAL = 'emotional'


class Difficulty(str, enum.Enum):
  EASY = 'easy'
  MEDIUM = 'medium'
  HARD = 'hard'


class Character(pydantic.BaseModel):
  name: str
  title: str
  description: str
  backstory: str
  strength: Attribute | None
  weakness: Attribute | None

  def to_markdown(self) -> str:
    return (
        f'- **{self.name}** - {self.title}: '
        f'<ins>{self.strength or ""}</ins> <del>{self.weakness or ""}</del> '
        f'{self.description} {self.backstory}'
    )


@dataclasses.dataclass
class Outcome:
  description: str
  encounter: Optional['Encounter']


@dataclasses.dataclass
class Action:
  description: str
  attribute: Attribute
  difficulty: Difficulty
  success: Outcome
  failure: Outcome

  def to_markdown(self):
    return '\n'.join([
        f'- **{self.attribute}** ({self.difficulty}): {self.description}',
        f'    - {self.success}',
        f'    - {self.failure}',
    ])


class CharacterChoice(pydantic.BaseModel):
  description: str
  attribute: Attribute
  outcome: str
  # next: 'LevelUp | None' = None


class Event(pydantic.BaseModel):
  name: str
  description: str


class Encounter(Event):
  difficulty: Difficulty
  actions: list[Action] | None = None

  def to_markdown(self):
    actions = self.actions or []
    action_bullets = '\n'.join(
        textwrap.indent(action.to_markdown(), '    ') for action in actions
    )
    bullet = f'- **{self.name}** ({self.difficulty}): {self.description}'
    return f'{bullet}\n{action_bullets}'


class LevelUp(Event):
  choices: list[CharacterChoice] | None


@dataclasses.dataclass
class Location:
  name: str
  description: str | None = None
  encounters: list[Encounter] | None = None

  def to_markdown(self) -> str:
    encounters = self.encounters or []
    encounter_bullets = '\n'.join(
        textwrap.indent(encounter.to_markdown(), '    ') for encounter in encounters
    )
    bullet = f'- **{self.name}**: {self.description}'
    return f'{bullet}\n{encounter_bullets}'


@dataclasses.dataclass
class Overview:
  name: str | None = None
  description: str | None = None

  def to_markdown(self) -> list[str]:
    return [
        f'# {self.name}',
        f'{self.description}',
    ]
