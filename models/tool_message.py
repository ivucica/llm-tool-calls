from models.message import Message
import pydantic

class ToolMessage(Message):
    """A message containing the response from a tool."""
    tool_call_id: str = pydantic.Field(..., description="The ID of the tool call")
