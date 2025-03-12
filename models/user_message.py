from models.message import Message
import typing
import pydantic

class UserMessage(Message):
    """A message sent by the user."""
    role: typing.Literal["user"] = pydantic.Field("user")
