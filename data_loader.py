import json
from pathlib import Path
from typing import Dict, List

from .models import Report, User
from .settings import ENGAGEMENTS_PATH, REPORTS_PATH, USERS_PATH


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


reports: List[Report] = [Report(**row) for row in load_json(REPORTS_PATH)]
users: Dict[str, User] = {u["id"]: User(**u) for u in load_json(USERS_PATH)}
engagements = load_json(ENGAGEMENTS_PATH)
