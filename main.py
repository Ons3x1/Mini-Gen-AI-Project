#Importations
from enum import Enum
from typing import Dict
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

#entities

class Category(Enum):
    BUG = 'bug report'
    TECH = 'technical difficulties '
    FEAT = 'feature requests'
    MISC= 'miscellaneous '

#outtput
class ResultRequest(BaseModel):
    category : Category
    summary: str
    extracted_data: str
    
#input
class SupportRequest(BaseModel):
    id: int
    name: str
    organization: str
    text: str

# Examplez
# Zaama db
support_requests = [
    SupportRequest(id=0, name="Ahmed Nasr", organization="E Corp", text="Hello, I need assistance with my order."),
    SupportRequest(id=1, name="Ons Nasr", organization="Go My Code", text="Can you provide more details about your services?"),
    SupportRequest(id=2, name="Sirine Nasr", organization="JCI Bardo", text="I have a question about my recent purchase."),
]

tech_support = []



@app.post("/support_request/")
def create_support_request(new_request: SupportRequest) -> SupportRequest:
    support_requests.append(new_request) #nhott fel "db"
    return new_request