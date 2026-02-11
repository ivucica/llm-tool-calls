import pydantic
import json
from models.function import Function

class ToolCall(pydantic.BaseModel):
    """A non-message part of the content: requiring a tool call to be made."""
    function: Function = pydantic.Field(..., description="The function to call")
    id: str = pydantic.Field(..., description="The ID of the tool call")
    type: str = pydantic.Field(..., description="The type of the tool call")
    # We may get a reply containing extra_content specific to a provider.
    # "extra_content": { "google": { "thought_signature": "<Signature A>" } },
    extra_content: dict = pydantic.Field(..., description="Extra content specific to a provider")

    # Special note about extra_content.google.thought_signature:
    # * "Since this user turn only contains a functionResponse (no fresh text),
    #   we are still in Turn 1 and must preserve <Signature_A>.
    # * This means we need to send this along in the tool_calls when we include
    #   them in the history.
