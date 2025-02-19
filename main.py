#Importations
from enum import Enum
from typing import Dict
from fastapi import FastAPI
from pydantic import BaseModel
import cohere
import nbimporter
from difflib import SequenceMatcher
from dotenv import load_dotenv
import os



#entities

#output
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


#Bringigng in protected variables from .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
co = cohere.ClientV2(API_KEY)


# generation function: extracts response only + bit of error handling
def get_cohere_response(content: str) -> str:
    messages = [{"role": "user", "content": content}]
    
    try:
        chat_response = co.chat(model="command-r-plus", messages=messages)
        
        if hasattr(chat_response, 'message') and hasattr(chat_response.message, 'content'):
            for item in chat_response.message.content:
                if hasattr(item, 'type') and item.type == 'text':
                    return item.text
        print('Cohere Response invalid')
        return None  #Type ou bien structure bizarre
    except Exception as e:
        print(f"Error calling Cohere API: {e}")
        return None 


# Prompting
Prompt0 = "You are a customer service agent working in IT, you receive support requests and provide technical support"
PromptCateg = """"There are 4 categories of a support request: bug report or technical difficulties or feature requests or miscellaneous, tell me which one
 is this one (only name the category): """
promptSummary = "give me a concise summary of this support request: "
promptDataBug = """As the support request in this case is a bug report, extract elements such as error codes, affected features/pages,
and triggering actions from this request only:"""
promptDataTech = """As the support request in this case is a technical difficulty, Extract details such as connection issues or
performance issues, or if the client has any difficulties navigating the platform in general from this request only:"""
promptDataFeat = """As the support request in this case is a feature request, Extract the name of the requested feature and any
context indicating urgency (low, medium, high) or benefits from this request only:  """
promptDataMisc = ""



#used instead on embedding/cosine... to compare categories and output of cohere
def most_similar(target, options):
    return max(options, key=lambda option: SequenceMatcher(None, target, option).ratio())

#function to categorize requests using prompting and func above
def categorize_request(text: str) -> Category:
    L = [str(Category.BUG), str(Category.FEAT), str(Category.TECH), str(Category.MISC)]
    category_map = {
        str(Category.BUG): Category.BUG,
        str(Category.FEAT): Category.FEAT,
        str(Category.TECH): Category.TECH,
        str(Category.MISC): Category.MISC,
    }
    categ = get_cohere_response(Prompt0 + PromptCateg + text)
    category_str = most_similar(categ, L)
    return category_map[category_str]

#function to summarize request in question by querying cohere
def generate_summary(text: str) -> str:
    return get_cohere_response(Prompt0 + promptSummary + text)



def process_support_request(support_request: SupportRequest) -> ResultRequest:
    
    category = categorize_request(support_request.text) 

    summary = generate_summary(support_request.text)

    extracted_data = '' #had to initialize it cz it wouldnt work otherwise
    
    if category == Category.BUG:
        extracted_data = get_cohere_response(Prompt0 + promptDataBug + support_request.text )
    elif category == Category.TECH:
        extracted_data = get_cohere_response(Prompt0 + promptDataTech + support_request.text )
    elif category == Category.FEAT:
        extracted_data = get_cohere_response(Prompt0 + promptDataFeat + support_request.text )
    elif category == Category.MISC:
        extracted_data = get_cohere_response('')

    return ResultRequest(category=category, summary=summary, extracted_data=extracted_data)





app = FastAPI()

########################################################################################################################################
# Example of db
support_requests = [
    SupportRequest(id=0, name="Ahmed Nasr", organization="E Corp", text="Hello, I need assistance with my order."),
    SupportRequest(id=1, name="Ons Nasr", organization="Go My Code", text="Can you provide more details about your services?"),
    SupportRequest(id=2, name="Sirine Nasr", organization="JCI Bardo", text="I have a question about my recent purchase."),
]
#########################################################################################################################################
@app.get("/support_request/")
def get_support_request():
    return {"Hi there! Ons here."}


@app.post("/support_request/", response_model=ResultRequest)
def create_support_request(new_request: SupportRequest) -> ResultRequest:
    support_requests.append(new_request)  # Add to "db"
    
    # Create a ResultRequest object
    result_request = process_support_request(new_request)   
    return result_request

