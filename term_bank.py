from dataclasses import dataclass
import dataclasses
from typing import Any

from content import StructuredContent, parse_structured_content, serialize_structured_content

def parse_definition(something: dict[str, Any]) -> StructuredContent:
    if something["type"] == "structured-content":
        return parse_structured_content(something["content"])
    else:
        raise ValueError(something)

def serialize_definition(content: StructuredContent) -> Any:
    return {
        "type": "structured-content",
        "content": serialize_structured_content(content)
    }

@dataclass(frozen=True, slots=True)
class Term:
    text: str
    reading: str
    tags: list[str]
    inflection_rules: list[str]
    popularity_score: int
    definitions: list[StructuredContent]
    sequence_number: int
    tags2: list[str]

    @staticmethod
    def parse(values: list[Any]) -> "Term":
        return Term(
            text=values[0],
            reading=values[1],
            tags=values[2].split(),
            inflection_rules=values[3].split(),
            popularity_score=int(values[4]),
            definitions=list(map(parse_definition, values[5])),
            sequence_number=int(values[6]),
            tags2=values[7].split()
        )

    def serialize(self) -> list[Any]:
        return [
            self.text,
            self.reading,
            " ".join(self.tags),
            " ".join(self.inflection_rules),
            self.popularity_score,
            list(map(serialize_definition, self.definitions)),
            self.sequence_number,
            " ".join(self.tags2)
        ]

def parse_term_bank(value: list[Any]) -> list[Term]:
    return list(map(Term.parse, value))

def serialize_term_bank(value: list[Term]) -> list[Any]:
    return list(map(Term.serialize, value))
