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

  def display(self):
    from IPython.display import display, Markdown

    def join_lines(lines):
      return '\n'.join(lines)

    assert self.overview is not None
    assert self.locations is not None
    assert self.characters is not None

    display(Markdown(f'''
# {self.overview.name}

{self.overview.description}

## Locations

{join_lines(
    f'- **{location.name}**: {location.description}'
    for location in self.locations
)}

## Characters

{join_lines(
    f'- **{character.name}** - {character.title}: <ins>{character.strength or ""}</ins> <del>{character.weakness or ""}</del> {character.description}'
    for character in self.characters
)}
    '''))
