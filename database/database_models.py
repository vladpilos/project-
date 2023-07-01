from pydantic import BaseModel


class DatabaseUser(BaseModel):
    id: int
    email: str
    password: str
    is_admin: int


class DatabaseEvent(BaseModel):
    id: int
    name: str
    date: float
    price: float
    seats_available: int


class DatabaseReservation(BaseModel):
    user_id: int
    event_id: int
    count: int
