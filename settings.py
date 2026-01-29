from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)

DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "app.db"

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
