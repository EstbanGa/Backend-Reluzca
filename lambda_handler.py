"""Handler para AWS Lambda con FastAPI."""

from mangum import Mangum
from main import app

_mangum = Mangum(app, lifespan="off")


def handler(event, context):
    # Warm-up event desde EventBridge — retorna rápido sin procesar HTTP
    if event.get("source") == "aws.events":
        return {"statusCode": 200, "body": "warm"}
    return _mangum(event, context)
