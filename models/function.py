import pydantic
import json

class Function(pydantic.BaseModel):
    """A non-message part of the content: requiring a function call to be made."""
    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True,
    )
    name: str = pydantic.Field(..., description="The name of the function")
    # It's actually a JSON encoded string containing a dict.
    #arguments: dict[str, any] = pydantic.Field(..., description="The arguments to call the function with")
    arguments: str = pydantic.Field(..., description="The arguments to call the function with")

    def get_arguments(self) -> dict:
        """Return the arguments as a dictionary."""
        return json.loads(self.arguments)

    def set_arguments(self, arguments: dict[str, any]):
        """Set the arguments from a dictionary."""
        self.arguments = json.dumps(arguments)
