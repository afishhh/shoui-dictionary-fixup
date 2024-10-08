import dataclasses
from functools import reduce
import itertools
import json
import re
from pathlib import Path
import sys
from typing import AnyStr
from content import StructuredItem, LinkTag, StructuredContent, Tag, display
from term_bank import *
import zipfile


class DefinitionTransformer:
    def __init__(
        self,
        *,
        text_replacements: list[tuple[AnyStr, str]] = [],
        strip_text: bool = False,
    ) -> None:
        self.text_replacements = list(
            map(lambda pat: (re.compile(pat[0], re.M), pat[1]), text_replacements)
        )
        self.strip_text = strip_text

    def transform_tag(self, tag: Tag) -> StructuredContent:
        return dataclasses.replace(tag, content=self.transform(tag.content))

    def transform_link(self, tag: LinkTag) -> StructuredContent:
        return self.transform_tag(tag)

    def transform_text(self, text: str) -> StructuredContent:
        result = reduce(lambda c, r: r[0].sub(r[1], c), self.text_replacements, text)
        return result if not self.strip_text else result.strip()

    def transform(self, content: StructuredContent) -> StructuredContent:
        if isinstance(content, LinkTag):
            return self.transform_link(content)
        elif isinstance(content, Tag):
            return self.transform_tag(content)
        elif isinstance(content, str):
            return self.transform_text(content)
        elif isinstance(content, list):

            def transform_one(element: StructuredItem) -> list[StructuredItem]:
                result = self.transform(element)
                if not isinstance(result, list):
                    return [result]
                else:
                    return result

            return list(
                itertools.chain.from_iterable(
                    transform_one(element) for element in content
                )
            )


class DictionaryProcessor:
    def __init__(
        self,
        *,
        debug_term_definitions: bool = False,
        definition_transformer: DefinitionTransformer | None = None,
    ) -> None:
        self.debug_term_definitions = debug_term_definitions
        self.definition_transformer = definition_transformer

    def transform_term(self, term: Term) -> Term:
        if self.definition_transformer is not None:
            return dataclasses.replace(
                term,
                definitions=list(
                    map(self.definition_transformer.transform, term.definitions)
                ),
            )
        return term

    def _transform_term(self, term: Term) -> Term:
        newterm = self.transform_term(term)
        if self.debug_term_definitions:
            assert len(term.definitions) == 1
            print(f" --- term {term.text} --- ")
            print(f" -- original definition -- ")
            display(sys.stdout, term.definitions[0])
            print(f" -- new definition -- ")
            display(sys.stdout, newterm.definitions[0])
        return newterm

    def process_term_bank(self, bank: list[Term]) -> list[Term]:
        return list(map(self._transform_term, bank))


def path_json(path: Path) -> Any:
    with path.open("r") as f:
        return json.load(f)


def process(
    input: Path | str, output: Path | str, processor: DictionaryProcessor
) -> Path:
    input = Path(input)
    output = Path(output)
    assert input.is_dir()
    output.mkdir(exist_ok=True)

    for src in input.glob("*.json"):
        rel = src.relative_to(input)
        out = output / rel

        match rel.parts:
            case ("index.json",):
                index = path_json(src)
                index["revision"] = index["revision"] + "; cleaned up"
                index["author"] = index["author"] + ", cleaned up by afishhh"
                out.write_text(json.dumps(index))
            case (str(name),) if name.startswith("term_bank"):
                terms = parse_term_bank(path_json(src))
                terms = processor.process_term_bank(terms)
                out.write_text(
                    json.dumps(serialize_term_bank(terms), ensure_ascii=False)
                )
            case _:
                raise ValueError(rel)

    return output


def zip_in_place(path: Path):
    zippath = path.with_name(path.name + ".zip")
    with zipfile.ZipFile(zippath, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for file in path.glob("*"):
            out.writestr(str(file.relative_to(path)), file.read_text())


class 毎日のんびり日本語教師Transformer(DefinitionTransformer):
    def __init__(self) -> None:
        super().__init__(text_replacements=[])

    def transform_link(self, tag: LinkTag) -> StructuredContent:
        if tag.href.startswith("https://nihongonosensei.net/?p="):
            return []
        else:
            raise ValueError(tag)

    def transform_text(self, text: str) -> StructuredContent:
        if text.strip() == "---END---":
            return []
        elif text.isspace():
            return []
        return text


class 毎日のんびり日本語教師Processor(DictionaryProcessor):
    def __init__(self, *, debug_term_definitions: bool = False) -> None:
        super().__init__(
            debug_term_definitions=debug_term_definitions,
            definition_transformer=毎日のんびり日本語教師Transformer(),
        )


class JLPT文法解説まとめDefinitionTransformer(DefinitionTransformer):
    def __init__(self) -> None:
        super().__init__(
            text_replacements=[
                (r"この文型が登場する教科書\s*$", ""),
                (r"\(adsbygoogle = window.adsbygoogle \|\| \[\]\).push\({}\);\s*$", ""),
                # There is an extra newline after some of these
                (r"(\[JLPT レベル\]\n.*?)\n+", "\\1\n\n"),
            ],
            strip_text=True,
        )

    def transform_link(self, tag: LinkTag) -> StructuredContent:
        if tag.href.startswith("https://nihongokyoshi-net.com/"):
            return []
        raise ValueError(tag)


class JLPT文法解説まとめProcessor(DictionaryProcessor):
    def __init__(self, *, debug_term_definitions: bool = False) -> None:
        super().__init__(
            debug_term_definitions=debug_term_definitions,
            definition_transformer=JLPT文法解説まとめDefinitionTransformer(),
        )


class どんなとき使う日本語表現文型辞典DefinitionTransformer(DefinitionTransformer):
    def __init__(self) -> None:
        super().__init__(
            text_replacements=[
                (r"google\.com/search\?q.*$", ""),
                (
                    r"itazuraneko.neocities.org/grammar/donnatoki/mainentries.html.*$",
                    "",
                ),
            ],
            strip_text=True,
        )

    def transform_link(self, tag: LinkTag) -> StructuredContent:
        # These links make no sense to be included in yomitan
        if tag.href.startswith("?query="):
            return []
        raise ValueError(tag)


class どんなとき使う日本語表現文型辞典Processor(DictionaryProcessor):
    def __init__(
        self,
        *,
        debug_term_definitions: bool = False,
    ) -> None:
        super().__init__(
            debug_term_definitions=debug_term_definitions,
            definition_transformer=どんなとき使う日本語表現文型辞典DefinitionTransformer(),
        )


class 絵でわかる日本語DefinitionTransformer(DefinitionTransformer):
    def __init__(self) -> None:
        super().__init__(
            text_replacements=[
                (r"\n\s*?\n\s*?\n", "\n\n"),
                (r"――以上――\s*$", ""),
                (r"^\s*語学\(日本語\)ランキング\s*$", ""),
                (r"^\s*にほんブログ村\s*$", ""),
            ],
            strip_text=True,
        )

    def transform_link(self, tag: LinkTag) -> StructuredContent:
        if any(
            tag.href.removeprefix("https://").removeprefix("http://").startswith(key)
            for key in ("www.edewakaru.com/archives/", "edewakaru.blog.jp/archives/")
        ):
            return []
        raise ValueError(tag)


class 絵でわかる日本語Processor(DictionaryProcessor):
    def __init__(
        self,
        *,
        debug_term_definitions: bool = False,
    ) -> None:
        super().__init__(
            debug_term_definitions=debug_term_definitions,
            definition_transformer=絵でわかる日本語DefinitionTransformer(),
        )


zip_in_place(
    process(
        "./[Grammar] 毎日のんびり日本語教師 (nihongosensei).zip",
        "./transformed/[Grammar] 毎日のんびり日本語教師 (nihongosensei)",
        毎日のんびり日本語教師Processor(),
    )
)

zip_in_place(
    process(
        "./[Grammar] JLPT文法解説まとめ(nihongo_kyoushi).zip/",
        "./transformed/[Grammar] JLPT文法解説まとめ(nihongo_kyoushi)",
        JLPT文法解説まとめProcessor(),
    )
)

zip_in_place(
    process(
        "./[Grammar] どんなとき使う日本語表現文型辞典.zip/",
        "./transformed/[Grammar] どんなとき使う日本語表現文型辞典",
        どんなとき使う日本語表現文型辞典Processor(),
    )
)

zip_in_place(
    process(
        "./[Grammar] 絵でわかる日本語.zip/",
        "./transformed/[Grammar] 絵でわかる日本語",
        絵でわかる日本語Processor(),
    )
)
