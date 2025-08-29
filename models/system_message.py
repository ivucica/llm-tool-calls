import pydantic
import typing
from models.message import Message
from models.model_settings import ModelSettings

class SystemMessage(Message):
    """System prompt."""
    role: typing.Literal["system"] = pydantic.Field("system")
    settings: typing.Optional[ModelSettings] = pydantic.Field(None, description="The settings for the model", exclude_unset=True)
