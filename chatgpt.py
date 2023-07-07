from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.docstore.document import Document
from langchain.chat_models import AzureChatOpenAI
from fastapi import FastAPI ,File, UploadFile , Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import openai
import pandas as pd
# from models.openai import Question
import requests

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configure OpenAI API
openai.api_type = "azure"
openai.api_version = '2023-05-15'
openai.api_base = os.getenv('OPENAI_API_BASE')
openai.api_key = os.getenv("OPENAI_API_KEY")

class Question(BaseModel):
    question: str

from langchain.memory import MongoDBChatMessageHistory


def cognitive_search_api(query):
    headers = {'Content-Type': 'application/json','api-key': os.getenv("AZURE_SEARCH_KEY")}
    index_name = 'azureblob-indexksw'

    url = os.getenv('AZURE_SEARCH_ENDPOINT') + '/indexes/'+ index_name + '/docs'
    url += '?api-version=2021-04-30-Preview'
    url += '&search={}'.format(query) # 질문
    url += '&select=*'
    url += '&$top=1'  # 문서 개수 제한
    url += '&queryLanguage=ko-KR'
    url += '&queryType=semantic' # 의미 체계 검색
    url += '&semanticConfiguration=semantic-config'
    url += '&captions=extractive|highlight-false'

    print(url)
    resp = requests.get(url, headers=headers)
    search_results = resp.json() # 결과값
    
    if not search_results['value']:
        return '',''
    else:
        return search_results['value'][0]['merged_content'] , search_results['value'][0]['metadata_storage_name']

def getchain(session_id):
    template = """You are a chatbot having a conversation with a human.

    Based only on the following context and chat_history below. If the information is not available, write "I don't know"
    Given the following extracted parts of a long document and a question, create a detailed, step by step answer in Korean.

    {context}

    {chat_history}
    Human: {human_input}
    Chatbot:"""


    prompt = PromptTemplate(
        input_variables=["chat_history", "human_input", "context"], template=template
    )
    connection_string = os.getenv('MONGODB_CONNECTION_STRING')
    message_history = MongoDBChatMessageHistory(
        connection_string=connection_string, session_id=session_id
    )
    memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input", chat_memory=message_history)
    llm = AzureChatOpenAI(deployment_name='gpt-35-turbo', openai_api_version=openai.api_version,
                        temperature=0.0, max_tokens=1024)
    global chain
    chain = load_qa_chain(
        llm, chain_type="stuff", memory=memory, prompt=prompt
    )



@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    # context = [
    #     {"name": "Alice", "age": 25},
    #     {"name": "Bob", "age": 30},
    # ]
    return templates.TemplateResponse("chatgpt.html",{"request": request})

# @app.get("/")
# def home():
#     return "hi alice"

@app.get("/files", response_class=HTMLResponse)
def read_main(request: Request):
    context = [
        {"name": "Alice", "age": 25},
        {"name": "Bob", "age": 30},
    ]
    return templates.TemplateResponse("file_upload.html", {"request": request , "context": context})


@app.post("/qna/")
def get_qna(question: Question):
    # Provide the connection string to connect to the MongoDB database
    getchain('kkk-session')
    # qa = qa_global
    text, path = cognitive_search_api(question)
   
    docsconvert = []
    docsconvert.append(Document(page_content=text,
                        metadata={"source": path}))
    print(docsconvert)
    print(question)
    print(chain)
    response = chain({"input_documents": docsconvert, "human_input": str(question)}, return_only_outputs=True)
    answer = response['output_text']
    
    if not answer:
        return {"data": "answer not found"}
    return {"data": chain.memory.buffer}