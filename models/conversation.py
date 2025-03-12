import pydantic
import copy
import datetime
from models.message import Message

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

    def get_messages(self) -> list[Message]:
        """Get a _copy_ all the messages in the conversation."""
        return copy.deepcopy(self.messages)
