from dataclasses import dataclass


@dataclass
class Event:
    name: str
    date: float
    price: float
    seats_available: int
