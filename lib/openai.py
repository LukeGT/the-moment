from collections.abc import Mapping
from typing import Any, cast

import openai

from lib import serialisation
from lib import schema


def user_message(content: str):
  return {
      'role': 'user',
      'content': content,
  }


def assistant_message(data: Any):
  content = serialisation.serialise(data)
  return {'role': 'assistant', 'content': content}


def prompt_set_the_stage(theme: str):
  return user_message(
      f'Set the stage for a {theme} themed role playing game. '
      "Describe the region that this takes place in, make sure there's some "
      'driving catastrophe that will inspire our heroes to rise to the '
      'challenge, and finish by providing some hope that our heroes can chase. '
      'Be brief, limit your response to just a single paragraph of 3 sentences. '
      f'Format your response as a {serialisation.DESCRIPTION} object with '
      'attributes for the region\'s "name" and the "description" requested above. '
  )


def prompt_characters(character_num: int):
  return user_message(
      f'Please list the {character_num} heroes of this story, with their names '
      'and a one sentence bio describing their skills and background story. '
      'Give each character an optional strength and weakness, selected from '
      'the following options '
      'in roughly equal amounts: "mental", "physical", "emotional", or "null". '
      'Give each character a "title", a single word describing them. '
      f'Format it as a list of {serialisation.DESCRIPTION} objects with the '
      'properties "name", "title", "description", "strength" and "weakness". '
  )


def prompt_locations(location_num: int):
  return user_message(
      f'Please name and give a one sentence description of {location_num} '
      'important locations in this world. '
      f'Format your response as a list of {serialisation.DESCRIPTION} objects, '
      'with "name" and "description" attributes. '
  )


def prompt_encounters():
  return user_message(
      'For each of the above locations, describe three problematic encounters '
      'that the heroes will have to overcome when they visit that location. '
      'The first encounter should be "easy", the next "medium" and the last '
      '"hard". '
      'Give each encounter a one or two word name. Also give each a two sentence '
      'description addressed to the heroes detailing the problem at hand, and '
      'be sure to speak in the second person. Just describe the problem, not '
      'the solution. '
      f'Format your response as a nested list of {serialisation.DESCRIPTION} '
      'objects, with top level objects for each location with a "name" '
      'attribute, and a "encounters" attribute containing a list of encounter '
      'objects. Each has a "name", "description" and "difficulty" attribute. '
      'The "difficulty" attribute should be one of "easy", "medium" or "hard". '
  )


def prompt_create_actions():
  return user_message(
      'For the encounter above, outline three diverse potential actions that '
      'the heroes might try to take in order to overcome the challenge. Just '
      'describe the intended action, not the outcome. Use a single sentence '
      'for each, and be sure to speak in the plural second person. '
      'Label each action with the given "attribute" that best matches it, '
      'which can be "emotional", "physical" or "mental". Don\'t explicitly '
      'call out this attribute in the descriptions. '
      'Please also rate each action\'s difficulty based on its likelihood of '
      'working in the given encounter. Difficulty can be "easy", "medium" or '
      '"hard". '
      'Try to make all the attributes and difficulties for each action '
      'different from one another. '
      'For each action, spend two sentences describing two possible outcomes of '
      'that action, one where the heroes are successful and another where they '
      'fail. The outcomes should neatly conclude the narrative that began in '
      'the encounter\'s description. '
      f'Format your response as a list of {serialisation.DESCRIPTION} objects '
      'with "description", "attribute", "difficulty", "success" and "failure" '
      'attributes.'
  )


def get_response(messages: list[dict[str, str]]):
  print('Sending:', messages)
  completion = openai.ChatCompletion.create(
      model='gpt-3.5-turbo',
      messages=messages,
  )
  print(completion)
  return completion['choices'][0]['message']['content']  # type: ignore


def create_overview(theme: str) -> schema.Overview:
  response = get_response([prompt_set_the_stage(theme)])
  overview_json = serialisation.deserialise(response, dict[str, str])
  return schema.Overview(**overview_json)


def create_characters(
    theme: str, overview: schema.Overview, character_num: int
) -> list[schema.Character]:
  response = get_response([
      prompt_set_the_stage(theme),
      assistant_message(overview),
      prompt_characters(character_num),
  ])
  characters_json = serialisation.deserialise(response, list[dict[str, Any]])
  return [schema.Character(**character_json) for character_json in characters_json]


def create_locations(
    theme: str, overview: schema.Overview, location_num: int
) -> list[schema.Location]:
  response = get_response([
      prompt_set_the_stage(theme),
      assistant_message(overview),
      prompt_locations(location_num),
  ])
  locations_json = serialisation.deserialise(response, list[dict[str, Any]])
  return [schema.Location(**location_json) for location_json in locations_json]


def create_encounters(
    theme: str, overview: schema.Overview, locations: list[schema.Location]
) -> list[schema.Location]:
  stripped_locations = [_strip_location(location) for location in locations]
  response = get_response([
      prompt_set_the_stage(theme),
      assistant_message(overview),
      prompt_locations(len(locations)),
      assistant_message(stripped_locations),
      prompt_encounters(),
  ])
  locations_json = serialisation.deserialise(response, list[dict[str, Any]])
  return [
      schema.Location(
          name=location_json['name'],
          encounters=[
              schema.Encounter(**encounter_json)
              for encounter_json in location_json['encounters']
          ],
      )
      for location_json in locations_json
  ]


def create_actions(
    theme: str,
    overview: schema.Overview,
    location: schema.Location,
    encounter: schema.Encounter,
) -> list[schema.Action]:
  response = get_response([
      prompt_set_the_stage(theme),
      assistant_message(overview),
      prompt_locations(1),
      assistant_message([_strip_location(location)]),
      user_message('Describe an encounter at this location, formatted as JSON.'),
      assistant_message(_strip_encounter(encounter)),
      prompt_create_actions(),
  ])
  actions_json = serialisation.deserialise(response, list[dict[str, Any]])
  return [
      schema.Action(
          description=action_json['description'],
          attribute=schema.Attribute(action_json['attribute']),
          difficulty=schema.Difficulty(action_json['difficulty']),
          success=action_json['success'],
          failure=action_json['failure'],
      )
      for action_json in actions_json
  ]


def _strip_location(location: schema.Location) -> schema.Location:
  return serialisation.filter_keys(location, {'name', 'description'})


def _strip_encounter(encounter: schema.Encounter) -> schema.Encounter:
  return serialisation.filter_keys(encounter, {'name', 'description', 'difficulty'})
