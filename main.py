from fastapi import FastAPI ,File, UploadFile , Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import openai
import pandas as pd

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configure OpenAI API
openai.api_type = "azure"
openai.api_version = "2022-12-01"
openai.api_base = os.getenv('OPENAI_API_BASE')
openai.api_key = os.getenv("OPENAI_API_KEY")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # context = [
    #     {"name": "Alice", "age": 25},
    #     {"name": "Bob", "age": 30},
    # ]
    return templates.TemplateResponse("login.html",{"request": request})

# @app.get("/")
# def home():
#     return "hi alice"

@app.get("/files", response_class=HTMLResponse)
async def read_main(request: Request):
    context = [
        {"name": "Alice", "age": 25},
        {"name": "Bob", "age": 30},
    ]
    return templates.TemplateResponse("file_upload.html", {"request": request , "context": context})