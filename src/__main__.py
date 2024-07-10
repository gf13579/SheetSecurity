from fastapi import FastAPI
from fastapi import HTTPException, Request
from fastapi import Form
from fastapi import File
from fastapi import Header
from fastapi import Depends
from fastapi import Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from starlette import status
from tempfile import NamedTemporaryFile
from fastapi import UploadFile
from typing import Optional
from typing import IO
from loguru import logger
from dotenv import load_dotenv
from collections import OrderedDict
import os
import hashlib
import zipfile
import io
import lxml.etree as etree
import hashlib
import random
import string


LOGFILE_DEBUG = '/var/log/sheetsec-debug.log'
LOGFILE_INFO = '/var/log/sheetsec-info.log'
LOGFILE_WARN = '/var/log/sheetsec-warn.log'
LOGFILE_ERROR = '/var/log/sheetsec-error.log'

def clear_log_file(logfile):
    try:
        with open(logfile, 'w') as file:
            file.truncate(0)
        print(f"Cleared contents of {logfile}")
    except FileNotFoundError:
        print(f"File '{logfile}' not found.")
    except Exception as e:
        print(f"An error occurred while clearing {logfile}: {e}")

# Clear each log file before starting logging
clear_log_file(LOGFILE_DEBUG)
clear_log_file(LOGFILE_INFO)
clear_log_file(LOGFILE_WARN)
clear_log_file(LOGFILE_ERROR)

def debug_filter(record):
    return record["level"].name == "DEBUG"

logger.add(LOGFILE_INFO, level='INFO', format="{time} {level} {message}")
logger.add(LOGFILE_WARN, level='WARNING', format="{time} {level} {message}")
logger.add(LOGFILE_ERROR, level='ERROR', format="{time} {level} {message}")

# Log only debug messages (not info, warning and error too)
logger.add(LOGFILE_DEBUG, level='DEBUG', filter=debug_filter, format="{time} {level} {message}")


logger.info(f"Logging to {LOGFILE_INFO}")
logger.warning(f"Logging to {LOGFILE_WARN}")
logger.error(f"Logging to {LOGFILE_ERROR}")
logger.debug(f"Logging to {LOGFILE_DEBUG}")

logger.info(f"SheetSec starting: {__file__}")

logger.debug("Sourcing .env")
load_dotenv("src/.env")

# Retrieve values
API_KEY = os.getenv('API_KEY')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
ADMIN_USER = os.getenv('ADMIN_USER')
ADMIN_PASS = os.getenv('ADMIN_PASS')

# In-memory dictionary to store files using their MD5 hash as the key
file_storage = OrderedDict()

# Generate dodgy session cookie shared by all admins (hack)
random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
ADMIN_SESSION = hashlib.sha256(random_str.encode('utf-8')).hexdigest()

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

@app.get("/")
def home(request: Request, response: Response):
    response = templates.TemplateResponse(
        request=request, name="index.html"
    )
    
    return response

@app.get("/static/js/app.js", response_class=Response)
async def get_script():
    js_content = ""
    with open("src/static/js/app.js", "r") as file:
        js_content = file.read()
    return Response(content=js_content, media_type="application/javascript")


@app.get("/admin")
def login(request: Request):
    
    return templates.TemplateResponse(
       request=request, name="admin.html", context={})

@app.post("/admin")
async def login(request: Request, username: str = Form(...), password: Optional[str] = Form(None)):

    if username == ADMIN_USER:
        # deliberately flawed logic
        if password and password != ADMIN_PASS:
            logger.warning("Bad credentials provided for admin logon")
            return
        else:
            logger.info("Authenticated admin user")
    else:
        logger.warning("Bad username provided for admin logon")
    
    # Successful auth
    response = RedirectResponse(url="/server", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="session", value=ADMIN_SESSION, max_age=1800)  # 1800 seconds = 30 minutes
    return response



@app.get("/server")
def server(request: Request, session: str = Cookie(None)):
    if session is None:
        raise HTTPException(status_code=401, detail="Session cookie required")
    if session != ADMIN_SESSION:
        raise HTTPException(status_code=401, detail="Invalid session cookie")
    
    info_logs = ""
    with open(LOGFILE_INFO, 'r') as file:
        info_logs = file.read()
    
    return templates.TemplateResponse(
       request=request, name="server.html", context={"info_logs": info_logs})


# 1MB limit on file size as reported by the content-length header
async def valid_content_length(content_length: int = Header(..., lt=1_000_000)):
    return content_length

@app.post("/upload")
async def upload(file: UploadFile = File(...), file_size: int = Depends(valid_content_length)):
    global file_storage

    # From https://github.com/tiangolo/fastapi/issues/362
    # read it in chunks in case we've been sent more than the content-length header suggests
    real_file_size = 0
    temp: IO = NamedTemporaryFile(delete=False)
    for chunk in file.file:
        real_file_size += len(chunk)
        if real_file_size > file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too large"
            )
        temp.write(chunk)
    temp.close()
    
    # Now read the contents of the temporary file into memory
    with open(temp.name, 'rb') as temp_file:
        file_contents = temp_file.read()

    # Validate that the file is a zip file
    if not zipfile.is_zipfile(io.BytesIO(file_contents)):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid zip file.")

    # Extract and read the .musicxml file within the zip file
    with zipfile.ZipFile(io.BytesIO(file_contents)) as zip_file:
        # Find the .musicxml file
        musicxml_filename = None
        for filename in zip_file.namelist():
            if filename.endswith('.musicxml'):
                musicxml_filename = filename
                break
        
        if not musicxml_filename:
            raise HTTPException(status_code=400, detail=".musicxml file not found in the uploaded zip file.")

        with zip_file.open(musicxml_filename) as musicxml_file:
            musicxml_contents = musicxml_file.read()

    # Detect and decode the file if it is in UTF-16 encoding
    try:
        musicxml_contents = musicxml_contents.decode('utf-8')
    except UnicodeDecodeError:
        musicxml_contents = musicxml_contents.decode('utf-16')

    musicxml_contents = add_watermark(musicxml_contents)

    # Limit the file_storage dict to the 10 most recent items (9 + the new one)
    if len(file_storage) > 10:
        file_storage = OrderedDict(list(file_storage.items())[-9:])

    # Store the file contents in the dictionary using the hash as the key
    file_hash = hashlib.md5(musicxml_contents.encode("utf-8")).hexdigest()
    file_storage.update({file_hash: musicxml_contents})

    return JSONResponse(content={"file_hash": file_hash, "message": "File uploaded and stored successfully"})


@app.get("/files/{file_hash}")
async def get_file(file_hash: str):
    if file_hash in file_storage:
        file_contents = file_storage[file_hash]
        headers = {'Content-Disposition': f'attachment; filename="{file_hash}.musicxml"'}
        # for testing
        # headers = {}
        return Response(content=file_contents, media_type="application/xml", headers=headers)
    raise HTTPException(status_code=404, detail="File not found")


def add_watermark(musicxml_contents):

    # Detect the encoding of the input XML
    if 'encoding="UTF-16"' in musicxml_contents:
        encoding = 'utf-16'
    else:
        encoding = 'utf-8'

    parser = etree.XMLParser(resolve_entities=True)
    root = etree.fromstring(musicxml_contents.encode(encoding), parser=parser)

    # Generate a random string for the (currently fake) watermark
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    watermark = hashlib.sha256(random_str.encode(encoding)).hexdigest()
    watermark_comment = f"{watermark}"

    # Insert the watermark comment towards the end of the XML
    # We assume 'root' is the top-level element of your XML
    root.append(etree.Comment(watermark_comment))

    # Serialize the modified XML back to a string
    modified_xml = etree.tostring(root, encoding='utf-16', xml_declaration=True).decode('utf-16')

    return modified_xml