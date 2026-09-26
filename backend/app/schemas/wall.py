from pydantic import BaseModel


class WallUpdate(BaseModel):
    name: str | None = None
    perimeter: float | None = None
    height: float | None = None
    note: str | None = None
