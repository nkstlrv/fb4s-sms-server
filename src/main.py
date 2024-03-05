import os
import json
import uvicorn
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI
from schemas.fub_webhook_schemas import EventSchema
from logs.logging_config import logger
from logs.logging_utils import log_server_start, log_server_stop
from views.sms_views import send_note_to_buyer_by_sms_view
# from utils.utils import backup_request_response


load_dotenv()

SERVER_PORT = os.getenv("SERVER_PORT")
SERVER_HOST = os.getenv("SERVER_HOST")


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    log_server_start()


@app.on_event("shutdown")
async def shutdown_event():
    log_server_stop()


@app.get("/")
async def index():
    logger.info(f"{index.__name__} -- INDEX ENDPOINT TRIGGERED")
    return {"success": True, "message": "SMS Engine Index"}


@app.post("/sms")
async def sms(request: EventSchema):

    payload = dict(request)

    logger.info(f"{sms.__name__} -- SMS ENDPOINT TRIGGERED")
    logger.info(f"{sms.__name__} -- RECEIVED PAYLOAD - {payload}")

    note_ids = request.resourceIds
    if note_ids:
        result = send_note_to_buyer_by_sms_view(note_ids[0])

    logger.info(f"{sms.__name__} -- SMS RESPONSE DATA - {result}")

    backup_data = {
        "request": payload,
        "response": result,
        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M UTC")
    }

    # temporary backing up data to json
    with open("database/backups.json", "a+") as f:
        backups = json.load(f)
        if not isinstance(backups, list):
            backups = []
        backups.append(backup_data)
        f.seek(0)
        json.dump(backups, f)
        logger.info(f"{sms.__name__} -- BACKUP DATA")

    return {
        "success": True if result["sms_sent"] else False,
        "data": result
        }


if __name__ == "__main__":
    uvicorn.run(app=app, port=int(SERVER_PORT), host=SERVER_HOST)
