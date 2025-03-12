import pydantic
import typing

class ToolResponseError(pydantic.BaseModel):
    """A non-message part of the content, indicating an error from the tool."""
    status: typing.Literal["error"] = pydantic.Field("error")
    message: str = pydantic.Field(..., description="Error message")
