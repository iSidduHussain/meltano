import abc

from typing.io import TextIO
from typing import Union
from elt.schema import Schema


class Serializer:
    def __init__(self, schema_or_name: Schema.Basis):
        self._schema = Schema.extend(schema_or_name)

    @property
    def schema(self):
        return self._schema

    def loads(self, raw: str) -> 'Serializer':
        raise NotImplementedError

    def load(self, reader: TextIO) -> 'Serializer':
        return loads(reader.read())

    def dumps(self) -> str:
        raise NotImplementedError

    def dump(self, writer: TextIO):
        writer.write(self.dumps(self.schema))
