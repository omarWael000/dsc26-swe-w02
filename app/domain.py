"""Parcel lifecycle rules for Tawseel.

Pure Python: do not import fastapi, starlette, pydantic or sqlalchemy here
(a hidden test checks). Keep the names below exactly as they are.
"""
from dataclasses import dataclass
from enum import StrEnum

MAX_ATTEMPTS = 3


class ParcelState(StrEnum):
    CREATED = "created"
    OUT_FOR_DELIVERY = "out_for_delivery"
    FAILED_ATTEMPT = "failed_attempt"
    DELIVERED = "delivered"
    RETURNED = "returned"


class EventType(StrEnum):
    DISPATCH = "dispatch"
    DELIVER = "deliver"
    FAIL = "fail"
    RETURN = "return"


class InvalidTransition(Exception): ...


@dataclass(frozen=True)
class Parcel:
    id: str
    merchant_ref: str
    cod_amount_piastres: int
    address_text: str
    state: ParcelState = ParcelState.CREATED
    attempts: int = 0


def apply_event(parcel: Parcel, event: EventType) -> Parcel:
    """Return a new Parcel. Raise InvalidTransition if the event is not allowed."""

    new_state= parcel.state
    new_attempts= parcel.attempts

    if parcel.state == ParcelState.CREATED and event == EventType.DISPATCH:
        new_state = ParcelState.OUT_FOR_DELIVERY
        new_attempts+=1

    elif parcel.state == ParcelState.OUT_FOR_DELIVERY and event == EventType.DELIVER:
        new_state = ParcelState.DELIVERED

    elif parcel.state == ParcelState.OUT_FOR_DELIVERY and event == EventType.FAIL:
        new_state = ParcelState.FAILED_ATTEMPT

    elif parcel.state == ParcelState.FAILED_ATTEMPT and event== EventType.DISPATCH and parcel.attempts<MAX_ATTEMPTS:
        new_state= ParcelState.OUT_FOR_DELIVERY
        new_attempts+=1

    elif parcel.state == ParcelState.FAILED_ATTEMPT and event == EventType.RETURN:
            new_state = ParcelState.RETURNED

    else:
        raise InvalidTransition(
            f"Event '{event}' is not allowed for state '{parcel.state}'"
        )

    return Parcel(
        id=parcel.id,
        merchant_ref=parcel.merchant_ref,
        cod_amount_piastres=parcel.cod_amount_piastres,
        address_text=parcel.address_text,
        state=new_state,
        attempts=new_attempts
    )
        

    
