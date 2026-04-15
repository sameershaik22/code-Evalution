from __future__ import annotations
import re
from typing import List ,Literal
import logging

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger('tokenizer')

Language = Literal['python' , 'c', 'c++', 'javascript' , 'java']

class Codetokenizer:

    _token_pattern = re.compile(
    r"""                                      #A regular expression to identify tokens, and also compiled only once accross all the calls, so there is no redundant compilations again.
    [A-Za-z_][A-Za-z0-9_]*   |  # identifiers
    \d+\.\d+                |  # floating point numbers
    \d+                     |  # integers
    ==|!=|<=|>=|<<|>>       |  # multi-character operators
    [+\-*/%&|^~<>]=?        |  # operators
    [(){}\[\],.;:]             # punctuation
    """,
    re.VERBOSE,
    )

    def tokenize(self, code:str, language:Language) -> List[str]:

        if code == None:
            logger.warning('Canidate Code is empty')
            return []
        normalized_code = self._normalize(code, language)

        if normalized_code == None:
            logger.warning('Normalized code is empty, maybe tokenization was wrong')
            return []
        return self._token_pattern.findall(normalized_code)


    @staticmethod
    def _normalize(code:str , language: Language) -> str:
        code = code.lower()

        if language == "python" :
            code = re.sub(r"#.*", "", code)

        else:
            code = re.sub(r"//.*", "", code)
            code = re.sub(r"/\*[\s\S]*?\*/", "", code)

        return code
