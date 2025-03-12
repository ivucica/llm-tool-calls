import pydantic
from models.date_object import DateObject

class DateSubtractRequest(pydantic.BaseModel):
    """
    Compute difference in years. Process input dates as timestamps, subtract
    timestamps, and return how many years passed, rounded down. Useful to
    compute age. If the dates are fetched from a different source, do not
    provide the inputs until you received them from a different function call.
    """
    later_date: DateObject = pydantic.Field(...,
        description="Later (newer) of the two input dates (must be valid)."
    )
    earlier_date: DateObject = pydantic.Field(...,
        description="Earlier (older) of the two input dates (must be valid)."
    )
    reason: str = pydantic.Field(...,
        description=(
            "Reason for date subtraction, e.g. 'calculate age' or 'compute"
            " difference between first showing of X and birth of Y.")
    )

    class Config:
        extra = pydantic.Extra.forbid
