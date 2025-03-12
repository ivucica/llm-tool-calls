import pydantic
import typing

class ToolResponseSuccess(pydantic.BaseModel):
    """A non-message part of the content: success and response from the tool."""
    status: typing.Literal["success"] = pydantic.Field("success")
    content: str = pydantic.Field(..., description="The content of the tool response")
    title: str = pydantic.Field(..., description="The title of the tool response")
