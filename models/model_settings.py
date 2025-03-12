import pydantic

class ModelSettings(pydantic.BaseModel):
    """Settings for the model."""
    # Exclude unset does not seem to do anything here. it seems to be an
    # argument to serializers, not to Field or model itself.
    max_tokens: int|None = pydantic.Field(None, description="The maximum number of tokens to generate", exclude_unset=True)
