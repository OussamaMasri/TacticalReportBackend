from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
REPORTS_PATH = DATA_DIR / "reports.json"
USERS_PATH = DATA_DIR / "users.json"
ENGAGEMENTS_PATH = DATA_DIR / "engagements.json"

WEIGHTS = {
    "purchase_cat": 10.0,
    "purchase_tag": 6.0,
    "view_cat": 4.0,
    "view_tag": 2.5,
    "view_long_bonus": 2.0,
    "campaign_click": 2.0,
    "campaign_open": 1.0,
    "bookmark": 2.5,
    "tag_match": 1.8,
    "focus_cat": 3.0,
    "focus_tag": 2.0,
}
