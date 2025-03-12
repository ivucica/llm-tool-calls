import pydantic

class DateObject(pydantic.BaseModel):
    """
    Year, month and date for one of the input dates. Must be a valid date
    and all fields must be non-null. Optional: what the date represents
    ('birthday of X', 'end of Y', etc.) and where the date came from.
    """
    # Note: these hints end up being "anyOf" instead of just "type": ["string",
    # "null"] as is documented to be expected.
    # Note: while that works on local models, Gemini refuses this schema.
    label: str = pydantic.Field( #typing.Optional[str] = pydantic.Field(
        ..., description="What the date represents (null or string)."
    )
    origin: str = pydantic.Field( # typing.Optional[str] = pydantic.Field(
        ..., description="Where the date came from (null or string)."
    )
    year: int = pydantic.Field(..., description="Year (non-null int).")
    month: int = pydantic.Field(..., description="Month (non-null int).")
    day: int = pydantic.Field(..., description="Day (non-null int).")

    class Config:
        extra = pydantic.Extra.forbid  # Additional properties not allowed
