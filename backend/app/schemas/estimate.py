from typing import List

from pydantic import BaseModel, Field


class EstimateRequest(BaseModel):
    wall_id: int
    roll_id: int
    save: bool = False
    note: str = ""


class FloorGroup(BaseModel):
    floor: str = Field(..., min_length=1)
    wall_ids: List[int] = Field(..., min_length=1)


class FloorStackRequest(BaseModel):
    roll_id: int
    floors: List[FloorGroup] = Field(..., min_length=1)
    save: bool = False
    note: str = ""
