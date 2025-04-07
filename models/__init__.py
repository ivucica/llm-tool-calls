# This file is intentionally left mostly empty to make the `models` directory a package.

# Import from current package.
from .message import Message
from .user_message import UserMessage
from .assistant_message import AssistantMessage
from .system_message import SystemMessage
from .tool_message import ToolMessage


def dict_to_message(message: dict) -> Message:
    """Convert to the correct type based on the role."""
    if 'role' not in message:
        # Create base class.
        message = Message(**message)
    elif message["role"] == "user":
        message = UserMessage(**message)
    elif message["role"] == "assistant":
        message = AssistantMessage(**message)
    elif message["role"] == "system":
        message = SystemMessage(**message)
    elif message["role"] == "tool":
        message = ToolMessage(**message)
    else:
        print(f"Unknown role: {message['role']}")
        message = Message(**message)
    return message
