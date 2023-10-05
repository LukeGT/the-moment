from typing import Any

import contextlib
import dataclasses
import yaml
import json

import openai

from lib import schema


def user_message(content: str):
    return {
        "role": "user",
        "content": content,
    }

def assistant_message(content: str | Any):
    if dataclasses.is_dataclass(content):
        content = dataclasses.asdict(content)
    if not isinstance(content, str):
        content = json.dumps(content)
    return {
        'role': 'assistant',
        'content': content
    }


def prompt_set_the_stage(theme: str):
    return user_message(
        f"Set the stage for a {theme} themed role playing game. "
        "Describe the region that this takes place in, make sure there's some "
        "driving catastrophe that will inspire our heroes to rise to the challenge, "
        "and finish by providing some hope that our heroes can chase. "
        "Be brief, limit your response to just a single paragraph of 3 sentences. "
        "Format your response as a YAML object with attributes for the region's "
        '"name" and the "description" requested above. '
    )


def prompt_locations(location_num: int):
    return user_message(
        f"Please name and give a one sentence description of {location_num} important locations in this world. "
        'Format your response as a list of YAML objects, with "name" and "description" attributes. '
    )


def prompt_characters(character_num: int):
    return user_message(
        f'Please list the {character_num} heroes of this story, with their names and a one sentence bio describing their skills and background story. '
        'Give each character an optional strength and weakness, selected from the following options in roughly equal amounts: "mental", "physical", "emotional", or "null". '
        'Give each character a "title", a single word describing them. '
        'Format it as a list of YAML objects with the properties "name", "title", "description", "strength" and "weakness".'
    )


def get_response(messages: list[dict[str, str]]):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return completion["choices"][0]["message"]["content"]


def parse_response(response: str):
    try:
      return yaml.safe_load(response)
    except:
      print(f'Failed to parse YAML from AI: {response}')
      raise


def create_overview(theme: str) -> schema.Overview:
    response = get_response([prompt_set_the_stage(theme)])
    overview_json = parse_response(response)
    return schema.Overview(**overview_json)


def create_locations(
    theme: str, overview: schema.Overview, location_num: int
) -> list[schema.Location]:
    response = get_response(
        [
            prompt_set_the_stage(theme),
            assistant_message(overview),
            prompt_locations(location_num),
        ]
    )
    locations_json = parse_response(response)
    return [
        schema.Location(**location_json)
        for location_json in locations_json
    ]

def create_characters(
    theme: str, overview: schema.Overview, character_num: int
) -> list[schema.Character]:
    response = get_response(
        [
            prompt_set_the_stage(theme),
            assistant_message(overview),
            prompt_characters(character_num),
        ]
    )
    characters_json = parse_response(response)
    return [
        schema.Character(**character_json)
        for character_json in characters_json
    ]
