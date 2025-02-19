#Importations
from enum import Enum
from typing import Dict
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from typing import Union
import cohere
import nbimporter
from difflib import SequenceMatcher
from dotenv import load_dotenv
import os



#entities

#input
class SupportRequest(BaseModel):
    id: int
    name: str
    organization: str
    text: str


#output
class Category(Enum):
    BUG = 'bug report'
    TECH = 'technical difficulties '
    FEAT = 'feature requests'
    MISC= 'miscellaneous '

#output
class ExtractedData(BaseModel):
    pass


#ExtractedData
class BugReportData(BaseModel):
    error_codes: Optional[str]
    affected_features: Optional[str]
    triggering_actions: Optional[str]
#ExtractedData
class TechnicalDifficultiesData(ExtractedData):
    connection_issues: Optional[str] 
    performance_issues: Optional[str]
    navigation_difficulties: Optional[str]   

class Urgency(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'highh'
 
#ExtractedData
class FeatureRequestData(ExtractedData):
    feature_name: Optional[str] 
    urgency: Optional[Urgency] 
    benefits: Optional[str] 
    
#Extracted Data     
class MiscellaneousData(ExtractedData):
    pass



#Final outtput
class ResultRequest(BaseModel):
    category : Category
    summary: str
    extracted_data: Union[BugReportData, TechnicalDifficultiesData, FeatureRequestData, MiscellaneousData, None]
    
    



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
# Prompting
Prompt0 = "You are a customer service agent working in IT, you receive support requests and provide technical support"
PromptCateg = """
You are a customer service agent working in IT. Your task is to categorize support requests into one of the following categories:
1. **Bug Report**: When the user reports an issue or unexpected behavior in the software.
2. **Technical Difficulties**: When the user is struggling to use a feature or access functionality.
3. **Feature Requests**: When the user suggests or requests a new feature.
4. **Miscellaneous**: When the request does not fit into the above categories or is a mix of them.

Your response should only include the category name (e.g., "bug report", "technical difficulties", etc.).
Here is the support request: """
promptSummary = "Give me a concise summary of this support request:"
promptDataBug = """The support request in this case is a bug report, and it should have this structure:
{
  "error_codes": [list of error codes],
  "affected_features": [list of affected features],
  "triggering_actions": [list of actions that caused the bug]
} Here is the support request, give me the dictionary:"""
promptDataTech = """The support request in this case is a technical difficulty report, and it should have this structure::
{
  "connection_issues": [list of error codes],
  "performance_issues": [list of affected features],
  "navigation_difficulties": [list of actions that caused the bug]
}  Here is the support request, give me the dictionary:"""
promptDataFeat = """The support request in this case is a feature request, , and it should have this structure
{
  "feature_name": [list of error codes],
  "urgency": [low or medium or high],
  "benefits": [list of actions that caused the bug]
}. Here is the support request, give me the dictionary:"""





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

# Extraxt Data Functions
def extract_bug(text: str) -> BugReportData:
    error = get_cohere_response(Prompt0 + promptDataBug + 'make sure the response includes only error codes' )
    affect = get_cohere_response(Prompt0 + promptDataBug + 'make sure the response includes only affected features' )
    trig = get_cohere_response(Prompt0 + promptDataBug + 'make sure the response includes only triggering actions' )
    return BugReportData(error_codes=error, affected_features=affect, triggering_actions=trig)

def extract_tech(text: str) -> TechnicalDifficultiesData:
    connect = get_cohere_response(Prompt0 + promptDataFeat + 'make sure the response includes only connection issues' )
    perform = get_cohere_response(Prompt0 + promptDataFeat + 'make sure the response includes only performance issues' )
    navig = get_cohere_response(Prompt0 + promptDataFeat + 'make sure the response includes only navigation difficulties' )
    return TechnicalDifficultiesData(connection_issues=connect, performance_issues=perform, navigation_difficulties=navig)

def extract_feat(text: str) -> FeatureRequestData:
    feat = get_cohere_response(Prompt0 + promptDataFeat + 'make sure the response includes only the fequested feature name' )
    urg = get_cohere_response(Prompt0 + promptDataFeat + 'make sure the response includes only the urgency type' )
    benef = get_cohere_response(Prompt0 + promptDataFeat + 'make sure the response includes only the benefits of the requested feature' )
    return FeatureRequestData(feature_name=feat, urgency=Urgency.MEDIUM, benefits=benef)


def process_support_request(support_request: SupportRequest) -> ResultRequest:
    
    category = categorize_request(support_request.text) 

    summary = generate_summary(support_request.text)

    extracted_data = None
    if category == Category.BUG:
        extracted_data = extract_bug(support_request.text)
    elif category == Category.FEAT:
        extracted_data = extract_feat(support_request.text)
    elif category == Category.TECH:
        extracted_data = extract_tech(support_request.text)
    else:
        extracted_data == None


    return ResultRequest(category=category, summary=summary, extracted_data=extracted_data)





app = FastAPI()
########################################################################################################################################
# Example of db
support_requests = [
    SupportRequest(id=0, name="Ahmed Kabaw", organization="E Corp", text="Hello, I need assistance with my order."),
    SupportRequest(id=1, name="Ons Neir", organization="Go My Code", text="Can you provide more details about your services?"),
    SupportRequest(id=2, name="Sirine Alleni", organization="JCI Bardo", text="I have a question about my recent purchase."),
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

