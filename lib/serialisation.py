from typing import Any, Type, TypeVar

import dataclasses
import json
import pydantic

SerializedData = (
    dict[str, 'SerializedData'] | list['SerializedData'] | int | float | str
)

DESCRIPTION = 'JSON'


class DataclassEncoder(json.JSONEncoder):

  def default(self, data: Any):
    if dataclasses.is_dataclass(data):
      return {key: value for key, value in dataclasses.asdict(data).items() if value}
    return super().default(data)


def serialise(data: Any) -> str:
  if isinstance(data, pydantic.BaseModel):
    return data.json()
  elif not isinstance(data, str):
    return json.dumps(data, cls=DataclassEncoder)


OuterType = TypeVar('OuterType')


def deserialise(string: str, outer_type: Type[OuterType]) -> OuterType:
  string = string.removeprefix('```json')
  string = string.removeprefix('```')
  string = string.removesuffix('```')
  try:
    return json.loads(string)
  except:
    print(f'Failed to parse {DESCRIPTION} from AI:\n{string}\nEOF')
    raise


def filter_keys(data: Any, keys: set[str]):
  return type(data)(
      **{
          key: value
          for key, value in dataclasses.asdict(data).items()
          if key in keys
      }
  )
