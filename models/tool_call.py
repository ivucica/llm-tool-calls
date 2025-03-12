import pydantic
import json
from models.function import Function

class ToolCall(pydantic.BaseModel):
    """A non-message part of the content: requiring a tool call to be made."""
    function: Function = pydantic.Field(..., description="The function to call")
    id: str = pydantic.Field(..., description="The ID of the tool call")
    type: str = pydantic.Field(..., description="The type of the tool call")
