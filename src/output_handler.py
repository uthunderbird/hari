import typing
from textwrap import indent

from aidial_sdk.chat_completion import Choice
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import chain
from pydantic import BaseModel

from models.criteria_verification import Vacancy


class Yieldable(BaseModel):
    pass


YieldableT = typing.TypeVar('YieldableT', bound=Yieldable)


class Content(Yieldable):
    content: str


class Attachment(Yieldable):
    type: typing.Optional[str] = None
    title: typing.Optional[str] = None
    data: typing.Optional[str] = None
    url: typing.Optional[str] = None
    reference_url: typing.Optional[str] = None
    reference_type: typing.Optional[str] = None


# A hack to deal with history
history = []


def make_output_handler(choice: Choice, root_choice: Choice | None = None):
    @chain
    async def processor(response_stream: typing.AsyncIterable[YieldableT | str | AIMessageChunk] | str):
        if isinstance(response_stream, str):
            choice.append_content(response_stream)
            return
        async for chunk in response_stream:
            if isinstance(chunk, AIMessageChunk):
                chunk = chunk.content
            if isinstance(chunk, Vacancy):
                choice.append_content(f"{chunk.text}")
                return chunk
            elif not isinstance(chunk, Yieldable):
                assert isinstance(chunk, str), (f"Yielded chunk should be either Yieldable "
                                                f"instance or str, {type(chunk)} provided.")
                chunk = Content(content=chunk)
            if isinstance(chunk, Content):
                choice.append_content(**chunk.model_dump())
            elif isinstance(chunk, Attachment):
                history.append(chunk)
                root_choice.add_attachment(**chunk.model_dump())
            else:
                raise TypeError(f"Unknown yieldable type: {type(chunk)}")

    return processor
