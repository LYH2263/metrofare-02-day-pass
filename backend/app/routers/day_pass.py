from fastapi import APIRouter

from app.schemas.day_pass import DayPassConfig
from app.services.metro_service import MetroService

router = APIRouter(tags=["day-pass"])


@router.get("/day-pass")
def get_day_pass():
    with MetroService() as s:
        return s.day_pass()


@router.put("/day-pass")
def put_day_pass(body: DayPassConfig):
    with MetroService() as s:
        return s.update_day_pass(body.day.isoformat(), body.cap, body.enabled)
