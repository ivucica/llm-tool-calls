from models.message import Message
from models.tool_call import ToolCall
import pydantic
import typing

class AssistantMessage(Message):
    """A message generated by the model."""
    role: typing.Literal["assistant"] = pydantic.Field("assistant")
    tool_calls: list[ToolCall]|None = pydantic.Field([], description="The tool calls to be made", exclude_unset=True)
