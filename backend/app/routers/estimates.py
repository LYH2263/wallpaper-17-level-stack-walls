from fastapi import APIRouter, Query
from app.schemas.estimate import EstimateRequest, FloorStackRequest
from app.services import estimate_service, stack_service

router = APIRouter()


@router.get("/estimate")
def estimate_get(wall_id: int = Query(...), roll_id: int = Query(...), save: bool = False):
    return estimate_service.run_estimate(wall_id, roll_id, save, "")


@router.post("/estimate")
def estimate_post(body: EstimateRequest):
    return estimate_service.run_estimate(body.wall_id, body.roll_id, body.save, body.note)


@router.post("/estimate/stack")
def estimate_stack(body: FloorStackRequest):
    return stack_service.run_floor_stack(body.roll_id, body.floors, body.save, body.note)
