from fastapi import APIRouter, HTTPException
from app.repositories import walls as repo
from app.schemas.wall import WallUpdate

router = APIRouter()


@router.get("/walls")
def list_walls():
    return {"items": repo.list_walls()}


@router.get("/walls/{wall_id}")
def get_wall(wall_id: int):
    row = repo.get_wall(wall_id)
    if not row:
        raise HTTPException(404)
    return row


@router.patch("/walls/{wall_id}")
def update_wall(wall_id: int, body: WallUpdate):
    row = repo.get_wall(wall_id)
    if not row:
        raise HTTPException(404)
    repo.update_wall(wall_id, body.model_dump(exclude_unset=True))
    return repo.get_wall(wall_id)
