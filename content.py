from copy import copy
from dataclasses import dataclass
import dataclasses
from typing import Any, Literal, TextIO

type StructuredItem = Tag | str
type StructuredContent = list[StructuredItem] | StructuredItem

@dataclass(frozen=True, slots=True)
class Tag:
    tag: str
    style: dict[str, str]
    content: StructuredContent

@dataclass(frozen=True, slots=True)
class LinkTag(Tag):
    tag: Literal['a']
    href: str

def _parse_structured_item(object: Any) -> StructuredItem | None:
    if isinstance(object, str):
        return object
    elif isinstance(object, dict):
        assert all(key in (
            "tag",
            "style",
            "content",
            "href"
        ) for key in object.keys())
        if object["tag"] == "a":
            return LinkTag(
                tag=object["tag"],
                style=object.get("style", {}),
                content=object["content"],
                href=object["href"]
            )
        else:
            return Tag(
                tag=object["tag"],
                style=object.get("style", {}),
                content=object["content"]
            )

def parse_structured_content(object: Any) -> StructuredContent:
    if (item := _parse_structured_item(object)):
        return item
    elif isinstance(object, list):
        def parse_item(item: Any) -> StructuredItem:
            result = _parse_structured_item(item)
            assert result is not None
            return result
        return list(map(parse_item, object))
    assert False

def serialize_structured_content(content: StructuredContent) -> Any:
    match content:
        case str(v):
            return v
        case list(v):
            return list(map(serialize_structured_content, v))
        case Tag():
            result = dataclasses.asdict(content)
            result["content"] = serialize_structured_content(result["content"])
            return result
        case _:
            raise ValueError(content)


@dataclass
class _DisplayState:
    bold: bool = False
    italic: bool = False
    underline: bool = False

    def apply_style(self, style: dict[str, Any]) -> "_DisplayState":
        result = copy(self)
        if "fontWeight" in style:
            assert style["fontWeight"] == "bold"
            result.bold = True
        return result


def _display(output: TextIO , content: StructuredContent, state: _DisplayState) -> bool:
    output.write("\x1b[0")
    if state.bold:
        output.write(";1")
    if state.italic:
        output.write(";3")
    if state.underline:
        output.write(";4")
    output.write("m")
    ret = False
    match content:
        case [*items]:
            for item in items:
                ret = _display(output, item, state)
        case LinkTag(tag, style, content, href):
            assert style == {}
            output.write(f"\x1b]8;;{href}\x1b\\")
            newstate = dataclasses.replace(state, underline=True).apply_style(style)
            ret = _display(output, content, newstate)
            output.write("\x1b]8;;\x1b\\")
        case Tag(tag, style, content):
            assert tag == "span"
            ret = _display(output, content, state.apply_style(style))
        case str():
            output.write(content)
            ret = content.endswith("\n")
    output.write("\x1b[0m")
    return ret


def display(output: TextIO, content: StructuredContent):
    if not _display(output, content, _DisplayState()):
        output.write("\n")
