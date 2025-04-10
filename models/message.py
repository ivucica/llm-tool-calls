import typing
import pydantic


class MultimodalContent(pydantic.BaseModel):
    """Object that can be used to create multimodal content in a list."""
    # TODO: split into multiple classes and create a union.
    type: typing.Literal["text", "image_url", "video_url", "audio_url", "file_url", "html"] = pydantic.Field(..., description="The type of content")
    text: typing.Optional[str] = pydantic.Field(None, description="The text content (if applicable)", skip_defaults=True)
    image_url: typing.Optional[str] = pydantic.Field(None, description="The URL of the image (if applicable). Can be a base64 dataurl.", skip_defaults=True)
    video_url: typing.Optional[str] = pydantic.Field(None, description="The URL of the video (if applicable)", skip_defaults=True)
    audio_url: typing.Optional[str] = pydantic.Field(None, description="The URL of the audio (if applicable)", skip_defaults=True)
    file_url: typing.Optional[str] = pydantic.Field(None, description="The URL of the file (if applicable)", skip_defaults=True)
    html: typing.Optional[str] = pydantic.Field(None, description="The HTML content (if applicable)", skip_defaults=True)


class Message(pydantic.BaseModel):
    """A message in a conversation."""
    # TODO: create a union type for the Message subclasses, rename this one to MessageBase.
    role: str = pydantic.Field(..., description="The role of the message sender")
    # Permitted values for role:
    # * system: messages added by the model developer (in this case us!)
    # * developer: from the application developer (this is us here, too)
    # * user: input from end users, or generally data to provide to the model
    # * assistant: generated by the  model
    # * tool: generated by a program (code execution, an API call)
    content: str|list[MultimodalContent]|None = pydantic.Field(None, description="The content of the message (may be omitted if only tool calls are requested)", skip_defaults=True)
    message_id: typing.Optional[str] = pydantic.Field(default=None, exclude=True)
    parent_message_id: typing.Optional[str] = pydantic.Field(default=None, exclude=True)
    recipient: typing.Optional[str] = pydantic.Field(default=None, description="The recipient of the message, e.g. browser for general tool use, or functions.foo for JSON-formatted function calling", exclude_unset=True)

    # Example of multimodal content, as JSON:
    # [
    #     {"type": "text", "text": "What's in this image?"},
    #     {
    #         "type": "image_url",
    #         "image_url": {
    #             "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
    #         },
    #     },
    # ],
    #
    # or
    #   "url": f"data:image/jpeg;base64,{base64_image}",
