import pydantic
import copy
import datetime
import json
from models.message import Message
from models.system_message import SystemMessage
from models import dict_to_message  # Defined in __init__.py for now.

class Conversation(pydantic.BaseModel):
    """Represents a series of messages in a conversation."""
    messages: list[Message] = []

    def add_message(self, message: Message|dict):
        """Add a new message to the conversation, and assign message IDs."""
        if isinstance(message, dict):
            message = dict_to_message(message)
        elif not isinstance(message, Message):
            print(f"Unknown message type: {message} (type: {type(message)})")

        if not message.message_id:
            message.message_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(hash(message.content))
        if self.messages:
            message.parent_message_id = self.messages[-1].message_id
        # print(f" (adding message to conversation: role={message.role}, now {len(self.messages)} messages)")

        self.messages.append(copy.deepcopy(message))
        self.save_default_history()

    def get_messages(self) -> list[Message]:
        """Get a _copy_ all the messages in the conversation."""
        return copy.deepcopy(self.messages)

    def to_json(self) -> str:
        """Serialize the Conversation instance to a JSON string."""
        return self.json()

    @classmethod
    def from_json(cls, json_str: str) -> "Conversation":
        """Deserialize a JSON string to a Conversation instance."""
        return cls.parse_raw(json_str)

    def clear_history(self):
        """Clear the conversation history, keeping only the system prompt."""
        self.messages = [msg for msg in self.messages if isinstance(msg, SystemMessage)]
        self.save_default_history()

    def load_history(self, filename: str):
        """Load conversation history from a JSON file."""
        with open(filename, 'r') as f:
            loaded_conversation = Conversation.from_json(f.read())
        self.messages = loaded_conversation.messages
        self.save_default_history()

    def save_history(self, filename: str):
        """Save conversation history to a JSON file."""
        with open(filename, 'w') as f:
            f.write(self.to_json())

    def save_default_history(self):
        """Save default conversation history to a JSON file."""
        default_history_file = "default_history.json"
        with open(default_history_file, 'w') as f:
            f.write(self.to_json())
