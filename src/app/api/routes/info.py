from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/data-date")
async def get_data_date(request: Request):
    """Return the date of the data currently loaded."""
    return {"data_date": request.app.data_date}
