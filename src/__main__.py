from fastapi.responses import Response
from fastapi import Request
from fastapi import FastAPI
from fastapi import Form
from typing import Optional

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from dotenv import load_dotenv
import os

LOGFILE_DEBUG = '/var/log/sheetsec-debug.log'
LOGFILE_INFO = '/var/log/sheetsec-info.log'
LOGFILE_WARN = '/var/log/sheetsec-warn.log'
LOGFILE_ERROR = '/var/log/sheetsec-error.log'

logger.add(LOGFILE_DEBUG, level='DEBUG', format="{time} {level} {message}")
logger.add(LOGFILE_INFO, level='INFO', format="{time} {level} {message}")
logger.add(LOGFILE_WARN, level='WARNING', format="{time} {level} {message}")
logger.add(LOGFILE_ERROR, level='ERROR', format="{time} {level} {message}")

logger.info("SheetSec starting")

logger.debug("Reading env variables")
load_dotenv("src/.env")

# Retrieve values
API_KEY = os.getenv('API_KEY')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS = os.getenv('ADMIN_PASS')

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# SOME_VAL = os.environ.get("SOME_VAL")

@app.get("/")
def home(request: Request, response: Response):
    response = templates.TemplateResponse(
        request=request, name="index.html"
    )
    
    return response

@app.get("/dynamic/js/app.js", response_class=Response)
async def get_script():
    js_content = ""
    with open("src/dynamic/js/app.js", "r") as file:
        js_content = file.read()
    return Response(content=js_content, media_type="application/javascript")


@app.get("/admin")
def login(request: Request):
    
    return templates.TemplateResponse(
        # empty context for now as we're not populating any templated values
       request=request, name="admin.html", context={})

# @app.get('/favicon.ico', include_in_schema=False)
# async def favicon():
#     return FileResponse('src/static/favicon.ico')

@app.post("/logon")
async def login(request: Request, username: str = Form(...), password: Optional[str] = Form(None)):

    if username == ADMIN_USER:
        if password and password != ADMIN_PASS:
            logger.warning("Bad credentials provided for admin logon")
            return
        else:
            logger.info("Authenticated admin user")
    else:
        logger.warning("Bad username provided for admin logon")
    
    
    
    return templates.TemplateResponse(
        # empty context for now as we're not populating any templated values
       request=request, name="server.html", context={})
