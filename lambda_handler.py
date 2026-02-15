"""Handler para AWS Lambda con FastAPI."""

from mangum import Mangum
from main import app

# Mangum convierte la aplicación FastAPI para que funcione con Lambda
handler = Mangum(app, lifespan="off")
