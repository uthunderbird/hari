import typing

from aidial_sdk.chat_completion import Choice
from langchain_core.runnables import chain
from pydantic import BaseModel


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


def make_output_handler(choice: Choice):
    @chain
    async def processor(response_stream: typing.AsyncIterable[YieldableT | str] | str):
        if isinstance(response_stream, str):
            choice.append_content(response_stream)
            return
        async for chunk in response_stream:
            if not isinstance(chunk, Yieldable):
                assert isinstance(chunk, str), (f"Yielded chunk should be either Yieldable "
                                                f"instance or str, {type(chunk)} provided.")
                chunk = Content(content=chunk)
            if isinstance(chunk, Content):
                choice.append_content(**chunk.model_dump())
            elif isinstance(chunk, Attachment):
                choice.add_attachment(**chunk.model_dump())
            else:
                raise TypeError(f"Unknown yieldable type: {type(chunk)}")

    return processor
