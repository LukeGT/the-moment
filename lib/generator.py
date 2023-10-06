from collections.abc import Iterable

import dataclasses

from lib import schema
from lib import openai


LOCATION_NUM = 5
CHARACTER_NUM = 10


@dataclasses.dataclass
class CampaignGenerator:
  theme: str

  overview: schema.Overview | None = None
  characters: list[schema.Character] | None = None
  locations: list[schema.Location] | None = None

  def create_overview(self):
    if self.overview is not None:
      raise ValueError('Overview already exists.')

    self.overview = openai.create_overview(self.theme)
    return self.overview

  def create_locations(self):
    if self.overview is None:
      raise ValueError('No overview found.')

    self.locations = openai.create_locations(self.theme, self.overview, LOCATION_NUM)
    return self.locations

  def create_characters(self):
    if self.overview is None:
      raise ValueError('No overview found.')

    self.characters = openai.create_characters(self.theme, self.overview, CHARACTER_NUM)
    return self.characters

  def create_encounters(self):
    if self.overview is None:
      raise ValueError('No overview found')
    if self.locations is None:
      raise ValueError('No locations found')
    if any(location.encounters for location in self.locations):
      raise ValueError('Encounters already defined.')

    locations = openai.create_encounters(self.theme, self.overview, self.locations)
    for location, location_with_encounters in zip(self.locations, locations):
      if location.name != location_with_encounters.name:
        print('Name mismatch:', location, location_with_encounters)
      location.encounters = location_with_encounters.encounters

    return locations

  def create_actions(self, location_index: int, encounter_index: int):
    if self.overview is None:
      raise ValueError('No overview found')
    if self.locations is None:
      raise ValueError('No locations found')

    location = self.locations[location_index]

    if not location.encounters:
      raise ValueError('No encounters found.')

    encounter = location.encounters[encounter_index]

    actions = openai.create_actions(self.theme, self.overview, location, encounter)
    encounter.actions = actions
    return actions

  def display(self):
    from IPython.display import display
    from IPython.core.display import Markdown

    def join_lines(lines: Iterable[str]):
      return '\n'.join(lines)

    assert self.overview is not None

    markdown_paragraphs = self.overview.to_markdown() + [
        '## Locations',
        join_lines(location.to_markdown() for location in self.locations or []),
        '## Characters',
        join_lines(character.to_markdown() for character in self.characters or []),
    ]
    display(Markdown('\n\n'.join(markdown_paragraphs)))
