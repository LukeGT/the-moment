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
      f"Please list the {character_num} hero{'es' if character_num > 1 else ''}"
      ' of this story. Give each of them a "name" and a "title", a single word '
      'describing them. '
      'Give a one sentence "description" which details their appearance and '
      'skills. '
      'Also give one sentence which introduces the beginnings of a backstory '
      'which will be later developed. This should be some event in the '
      "character's past or a core belief that they are challenged and shaped "
      'by, but yet to be resolved. '
      'Give each a "strength" and "weakness", selected from the following '
      'options in roughly equal amounts: "mental", "physical", "emotional", or '
      'null. '
  )


def prompt_character_levelup_1():
  return user_message(
      'This character is now suddenly faced with an event relevant to their '
      'backstory, where they are presented with an important choice that '
      'changes the way they perceive their past, but still leaves them room to '
      'grow. Write a 3 sentence "description" of how this event arises, spoken '
      'in the second person, and do not elaborate on how the hero responds to '
      'the event here. When referring to important people or places, give them '
      'specific names. '
      'Give this event a two word "name". '
      'Also create a list of three "choices" that they can make in response to '
      'the event. '
      'Each choice will channel a specific "attribute", either "mental", '
      '"physical" or "emotional", which shapes the choice. '
      'Give each choice a "description", a single sentence spoken in the '
      'imperative second person which describes a potential choice for the '
      'hero, but does not describe how it resolves here. '
      'For each choice, provide a two sentence "outcome" which details '
      'how the hero\'s choice plays out and reshapes their perception of their '
      'backstory.'
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
      'for each, and be sure to speak in the imperative plural second person. '
      'Label each action with the given "attribute" that best matches it, '
      'which can be "emotional", "physical" or "mental". Don\'t explicitly '
      'call out this attribute in the descriptions. '
      "Please also rate each action's difficulty based on its likelihood of "
      'working in the given encounter. Difficulty can be "easy", "medium" or '
      '"hard". '
      'Try to make all the attributes and difficulties for each action '
      'different from one another. '
      'For each action, spend two sentences describing two possible outcomes of '
      'that action, one where the heroes are successful and another where they '
      'fail. The outcomes should neatly conclude the narrative that began in '
      "the encounter's description. "
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


def get_structured_response(messages: list[dict[str, str]], schema: Mapping[str, Any]):
  print('Sending:', messages)
  completion = openai.ChatCompletion.create(
      model='gpt-3.5-turbo',
      messages=messages,
      functions=[{
          'name': 'respond',
          'description': 'Provide the requested information.',
          'parameters': {'type': 'object', 'properties': {'value': schema}},
      }],
      function_call={'name': 'respond'},
  )
  print(completion)
  json_args = completion['choices'][0]['message']['function_call']['arguments']  # type: ignore
  parsed_args = serialisation.deserialise(json_args, dict[str, Any])
  return parsed_args['value']


def create_overview(theme: str) -> schema.Overview:
  response = get_response([prompt_set_the_stage(theme)])
  overview_json = serialisation.deserialise(response, dict[str, str])
  return schema.Overview(**overview_json)


def create_characters(
    theme: str, overview: schema.Overview, character_num: int
) -> list[schema.Character]:
  characters = get_structured_response(
      [
          prompt_set_the_stage(theme),
          assistant_message(overview),
          prompt_characters(character_num),
      ],
      {
          'type': 'array',
          'items': schema.Character.model_json_schema(),
      },
  )
  return [schema.Character(**character) for character in characters]


def create_character_levelup_1(
    theme: str, overview: schema.Overview, character: schema.Character
) -> schema.LevelUp:
  level_up = get_structured_response(
      [
          prompt_set_the_stage(theme),
          assistant_message(overview),
          prompt_characters(1),
          assistant_message(character),
          prompt_character_levelup_1(),
      ],
      schema.LevelUp.model_json_schema(),
  )
  return schema.LevelUp.model_validate(level_up)


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
