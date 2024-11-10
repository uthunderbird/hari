import typing
from functools import lru_cache
from pathlib import Path

from langchain_openai import ChatOpenAI

from models.verified_cv import ProbablyCV, ProbablyCVWithRawText
from prompts.validator_prompt import VALIDATOR_SYSTEM_PROMPT

DirectoryParser = typing.Callable[[Path | str], dict[str, str]]


def validate_cv(file_path: Path | str, content: str) -> ProbablyCVWithRawText:
    if isinstance(file_path, str):
        file_path = Path(file_path)
    if file_path.with_suffix('.json').exists():
        return ProbablyCVWithRawText.model_validate_json(file_path.with_suffix('.json').read_text())
    model = ChatOpenAI(model="gpt-4o").with_structured_output(ProbablyCV)
    result: ProbablyCV = model.invoke(
        [
            ('system', VALIDATOR_SYSTEM_PROMPT),
            ('user', content),
        ]
    )
    d = result.model_dump()
    d['raw_text'] = content
    final_result = ProbablyCVWithRawText(**d)
    file_path.with_suffix('.json').write_text(final_result.model_dump_json(indent=2))
    return final_result


@lru_cache
def validate_cvs(directory_parser: DirectoryParser, path: Path | str) -> dict[str, ProbablyCVWithRawText]:
    parsed_files = directory_parser(path)
    validated_cvs = {}
    for k, v in parsed_files.items():
        validated_cv = validate_cv(k, v)
        if validated_cv.is_cv:
            validated_cvs[k] = validated_cv
    return validated_cvs

if __name__ == '__main__':
    from doc_parser import parse_directory
    res = validate_cvs(parse_directory, '..\\cvs')
    pass
