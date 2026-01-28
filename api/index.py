from mangum import Mangum

# For Vercel serverless: project root is `backend/`, so main.py is sibling of api/
from main import app  # type: ignore  # noqa: E402

handler = Mangum(app, lifespan="off")
