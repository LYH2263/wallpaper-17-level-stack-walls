from pydantic import BaseModel


class EstimateRequest(BaseModel):
    wall_id: int
    roll_id: int
    save: bool = False
    note: str = ""


class FloorSpec(BaseModel):
    floor: str = ""
    wall_ids: list[int] = []


class FloorEstimateRequest(BaseModel):
    roll_id: int
    floors: list[FloorSpec]
    save: bool = False
    note: str = ""
