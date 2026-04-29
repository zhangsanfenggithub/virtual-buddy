from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class SimState:
    step: int
    sim_time: str
    glucose: float
    status: str
    meal_event: bool
    meal_cho: float
    alert: Optional[str]
    glucose_history: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
