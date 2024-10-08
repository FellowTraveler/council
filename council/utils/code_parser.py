from __future__ import annotations

import re
from typing import Iterable, List, Optional

from more_itertools import first, last


class CodeBlock:
    def __init__(self, language: Optional[str], code: str) -> None:
        self._language = language
        self._code = code

    @property
    def code(self) -> str:
        return self._code

    @property
    def language(self) -> Optional[str]:
        return self._language

    def is_language(self, language: str) -> bool:
        if self._language is None:
            return False
        return self._language.casefold() == language.casefold()


class CodeParser:
    @staticmethod
    def iter_code_blocs(language: Optional[str] = None, text: str = "") -> Iterable[CodeBlock]:
        return CodeParser._build_generator(language, text)

    @staticmethod
    def extract_code_blocs(language: Optional[str] = None, text: str = "") -> List[CodeBlock]:
        return list(CodeParser._build_generator(language, text))

    @staticmethod
    def find_first(language: Optional[str] = None, text: str = "") -> Optional[CodeBlock]:
        blocks = CodeParser._build_generator(language, text)
        return first(blocks, None)

    @staticmethod
    def find_last(language: Optional[str] = None, text: str = "") -> Optional[CodeBlock]:
        blocks = CodeParser._build_generator(language, text)
        return last(blocks, None)

    @staticmethod
    def _get_pattern(language: Optional[str]):
        return r"```([^\n]*)\n(.*?)\n?```" if language is None else rf"```({re.escape(language)})\n(.*?)\n?```"

    @staticmethod
    def _build_generator(language: Optional[str], text: str = "") -> Iterable[CodeBlock]:
        p = CodeParser._get_pattern(language)
        matches = re.finditer(p, text, re.DOTALL)
        for match in matches:
            yield CodeBlock(match.group(1), match.group(2))
