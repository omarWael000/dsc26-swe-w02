"""HTTP layer for the Tawseel parcel service.

The HTTP layer translates requests into calls to app.domain; the domain decides.
See README.md for the four operations, their operationIds and their errors.
"""

from dataclasses import asdict
from uuid import uuid4

from fastapi import FastAPI, HTTPException,Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from pydantic import BaseModel, ConfigDict, Field

from app.domain import EventType, InvalidTransition, Parcel, ParcelState, apply_event  # noqa: F401

class CreateParcelRequest(BaseModel):
    merchant_ref: str = Field(min_length=1, max_length=64)
    cod_amount_piastres: int = Field(ge=0, le=5_000_000)
    address_text: str = Field(min_length=1, max_length=500)


class ParcelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_ref: str
    cod_amount_piastres: int
    address_text: str
    state: ParcelState
    attempts: int


class ParcelEventRequest(BaseModel):
    type: EventType


def problem_response(
    status: int,
    title: str,
    detail: str | None = None,
    errors: list[dict] | None = None,
) -> JSONResponse:
    body = {
        "type": "about:blank",
        "title": title,
        "status": status,
    }

    if detail is not None:
        body["detail"] = detail

    if errors is not None:
        body["errors"] = errors

    return JSONResponse(
        status_code=status,
        content=body,
        media_type="application/problem+json",
    )


def create_app() -> FastAPI:
    """Return a new FastAPI app with its own empty in-memory store."""

    app = FastAPI(title="Tawseel Parcel Service")

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ):
        titles = {
            400: "Bad Request",
            404: "Not Found",
            409: "Conflict",
        }

        return problem_response(
            status=exc.status_code,
            title=titles.get(exc.status_code, "Error"),
            detail=str(exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        errors = [
            {
                "loc": list(error["loc"]),
                "msg": error["msg"],
            }
            for error in exc.errors()
        ]

        return problem_response(
            status=422,
            title="Unprocessable Content",
            errors=errors,
        )


    parcels: dict[str, Parcel] = {}
    merchant_refs: set[str] = set()
    creation_order: dict[str, int] = {}
    next_position = 0
    cursor_positions: dict[str, int] = {}

    @app.post(
        "/v1/parcels",
        response_model=ParcelResponse,
        status_code=201,
        operation_id="createParcel",
        responses={
            409: {"description": "Duplicate merchant reference"},
            422: {"description": "Invalid request body"},
        },
    )
    def create_parcel(payload: CreateParcelRequest, response: Response):
        
        nonlocal next_position
        if payload.merchant_ref in merchant_refs:
            raise HTTPException(
                status_code=409,
                detail="Duplicate merchant_ref",
            )

        parcel_id = f"pcl_{uuid4().hex}"

        parcel = Parcel(
            id=parcel_id,
            merchant_ref=payload.merchant_ref,
            cod_amount_piastres=payload.cod_amount_piastres,
            address_text=payload.address_text,
        )

        parcels[parcel_id] = parcel
        merchant_refs.add(parcel.merchant_ref)
        creation_order[parcel_id] = next_position
        next_position += 1

        response.headers["Location"] = f"/v1/parcels/{parcel_id}"
        return parcel


    @app.get(
        "/v1/parcels/{parcel_id}",
        response_model=ParcelResponse,
        operation_id="getParcel",
        responses={
            404: {"description": "Parcel not found"},
        },
    )
    def get_parcel(parcel_id: str):
        parcel = parcels.get(parcel_id)

        if parcel is None:
            raise HTTPException(
                status_code=404,
                detail="Parcel not found",
            )

        return parcel

    @app.post(
        "/v1/parcels/{parcel_id}/events",
        response_model=ParcelResponse,
        operation_id="recordParcelEvent",
        responses={
            404: {"description": "Parcel not found"},
            409: {"description": "Invalid state transition"},
            422: {"description": "Invalid event request"},
        },
    )

    def record_parcel_event(
        parcel_id: str,
        payload: ParcelEventRequest,
    ):
        parcel = parcels.get(parcel_id)

        if parcel is None:
            raise HTTPException(
                status_code=404,
                detail="Parcel not found",
            )

        try:
            updated_parcel = apply_event(parcel, payload.type)
        except InvalidTransition:
            raise HTTPException(
                status_code=409,
                detail="Invalid parcel state transition",
            )

        parcels[parcel_id] = updated_parcel
        return updated_parcel


    
    @app.get(
        "/v1/parcels",
        operation_id="listParcels",
        responses={
            200: {"description": "Parcels listed successfully"},
            400: {"description": "Invalid cursor"},
            422: {"description": "Invalid state or limit"},
        },
    )
    def list_parcels(
        state: ParcelState | None = None,
        limit: int = Query(default=20, ge=1, le=100),
        cursor: str | None = None,
    ):
        # Resolve the position to continue from.
        if cursor is None:
            after_position = -1
        else:
            if cursor not in cursor_positions:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid cursor",
                )
            after_position = cursor_positions[cursor]

        # Select matching parcels in their original creation order.
        matching = [
            parcel
            for parcel_id, parcel in parcels.items()
            if creation_order[parcel_id] > after_position
            and (state is None or parcel.state == state)
        ]

        matching.sort(
            key=lambda parcel: creation_order[parcel.id]
        )

        # Return at most 'limit' parcels.
        items = matching[:limit]
        next_cursor = None

        # Issue a cursor only if more matching items remain.
        if len(matching) > limit:
            last_position = creation_order[items[-1].id]
            next_cursor = uuid4().hex
            cursor_positions[next_cursor] = last_position

        return {
            "items": items,
            "next_cursor": next_cursor,
        }




    return app

app = create_app()






