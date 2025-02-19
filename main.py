#Importations
from enum import Enum
from typing import Dict
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from typing import Union
import cohere
import json
import nbimporter
from difflib import SequenceMatcher
from dotenv import load_dotenv
import os



#entities

# Input
class SupportRequest(BaseModel):
    id: int
    name: str
    organization: str
    text: str

# Output
class Category(Enum):
    BUG = 'bug report'
    TECH = 'technical difficulties'
    FEAT = 'feature requests'
    MISC = 'miscellaneous'

# Output
class ExtractedData(BaseModel):
    pass

# ExtractedData
class BugReportData(ExtractedData):
    error_codes: Optional[str]
    affected_features: Optional[str]
    triggering_actions: Optional[str]

# ExtractedData
class TechnicalDifficultiesData(ExtractedData):
    connection_issues: Optional[str]
    performance_issues: Optional[str]
    navigation_difficulties: Optional[str]

class Urgency(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'

# ExtractedData
class FeatureRequestData(ExtractedData):
    feature_name: Optional[str]
    urgency: Optional[Urgency]
    benefits: Optional[str]

# Extracted Data     
class MiscellaneousData(ExtractedData):
    pass

# Final output
class ResultRequest(BaseModel):
    category: Category
    summary: str
    extracted_data: Union[
        BugReportData, TechnicalDifficultiesData, FeatureRequestData, MiscellaneousData, None
    ]



# Prompts
PromptCateg = """
You are a customer service agent specializing in IT support. Categorize the following support request into one of these four categories:  
1. **Bug Report**: The user reports a software issue or unexpected behavior.  
2. **Technical Difficulties**: The user struggles to use a feature or access functionality.  
3. **Feature Request**: The user requests or suggests a new feature.  
4. **Miscellaneous**: The request does not clearly fit into a single category or is a mix of the above.  

**Examples:**  

- **Bug Report**  
  _Request: "I keep getting an error when I try to reset my password. It says 'Invalid token' and won’t let me proceed."_  
  **Category:** "bug report"  

- **Technical Difficulties**  
  _Request: "I can’t figure out how to export my reports. The option seems to be missing in my dashboard."_  
  **Category:** "technical difficulties"  

- **Feature Request**  
  _Request: "It would be great if there was a dark mode option for the app. It would make it easier to use at night."_  
  **Category:** "feature request"  

- **Miscellaneous**  
  _Request: "I’ve been having issues logging in, and I also think a multi-factor authentication feature would be useful."_  
  **Category:** "miscellaneous"  

Now categorize this request:  
"""

promptSummary = "You are a customer service agent working in IT, you receive support requests and provide technical support. Give me a concise summary of this support request:"
promptDataBug = """
You are a customer service agent specializing in IT support. Your task is to extract structured information from bug reports. Below is an example of a bug report and its corresponding structured data:

**Example Bug Report:**
"You are a customer service agent specializing in IT support. Your task is to extract structured information from bug reports. Below is an example of a bug report and its corresponding structured data:

**Example Bug Report:**
"I encountered an error while using the search feature. The error code is ERR123, and it happens whenever I try to search for a product with special characters. This affects the search functionality, and I can't find any products. Please fix this as soon as possible."

**Structured Data:**
{
  "error_codes": "ERR123",
  "affected_features": "Search functionality",
  "triggering_actions": "Searching for products with special characters"
}
---
Your task is to extract the following information from the new bug report and return it in the exact same structured format as the example above:
1. **error_codes**: Any error codes mentioned (if none, leave as null).
2. **affected_features**: The feature or functionality affected by the issue.
3. **triggering_actions**: The actions or conditions that trigger the issue.

Return the structured data in JSON format, exactly like the example above and if u don't have enough info, don't ask for more information, you can leave some features empty. Here is the bug report:
"""
promptDataTech = """
You are a customer service agent specializing in IT support. Your task is to extract structured information from technical difficulty reports. Below is an example of a technical difficulty report and its corresponding structured data:

**Example Technical Difficulty Report:**
"I'm experiencing frequent disconnections while using the platform. The website becomes very slow, and sometimes I can't navigate between pages properly. This is making it hard for me to complete my tasks."

**Structured Data:**
{
  "connection_issues": "Frequent disconnections while using the platform",
  "performance_issues": "Website becomes very slow",
  "navigation_difficulties": "Can't navigate between pages properly"
}

---
Your task is to extract the following information from the new technical difficulty report and return it in the exact same structured format as the example above:
1. **connection_issues**: Any mentions of connectivity problems (if none, leave as null).
2. **performance_issues**: Any mentions of performance slowdowns or lag (if none, leave as null).
3. **navigation_difficulties**: Any mentions of difficulties in navigating through the platform (if none, leave as null).

Return the structured data in JSON format, exactly like the example above and if u don't have enough info, don't ask for more information, you can leave some features empty. Here is the technical difficulty report:
"""

promptDataFeat = """
You are a customer service agent specializing in IT support. Your task is to extract structured information from feature requests. Below is an example of a feature request and its corresponding structured data:

**Example Feature Request:**
"I would love to have a dark mode option for the platform. It's really hard to use at night, and a dark theme would make it much more comfortable. This is quite important for me, as I work late hours."

**Structured Data:**
{
  "feature_name": "Dark mode",
  "urgency": "medium",
  "benefits": "More comfortable to use at night, Helpful for working late hours"
}

---
Your task is to extract the following information from the new feature request and return it in the exact same structured format as the example above:
1. **feature_name**: The name of the requested feature.
2. **urgency**: The urgency level (low, medium, or high) based on the user's request.
3. **benefits**:  The benefits the user mentions for requesting this feature.

Return the structured data in JSON format, exactly like the example above and even if you don't have enough info, don't ask for more information, you can leave some fields empty. Here is the feature request:
"""
    

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

# Small Scale Functions

def most_similar(target, options):
    return max(options, key=lambda option: SequenceMatcher(None, target, option).ratio())

#function to categorize requests using prompting and func above
def categorize_request(text: str) -> Category:
    L = ['bug report', 'feature requests', 'technical difficulties', 'miscellaneous']
    category_map = {
        'bug report': Category.BUG,
        'feature requests': Category.FEAT,
        'technical difficulties': Category.TECH,
        'miscellaneous': Category.MISC,
    }
    categ = get_cohere_response(PromptCateg + text)
    category_str = most_similar(categ, L)
    return category_map[category_str]

#function to summarize request in question by querying cohere
def generate_summary(text: str) -> str:
    return get_cohere_response(promptSummary + text)


## Parsing Functions:

def transform_to_json(input_str):
    # Remove the leading and trailing triple backticks and 'json' identifier
    json_str = input_str.strip('```json\n').strip('\n```')
    
    # Parse the JSON string into a Python dictionary
    json_data = json.loads(json_str)
    
    return json_data


def parse_bug_report(json_string: str):
    try:
        # Parse JSON string into a dictionary
        data = json.loads(json_string)

        # Extract values with safe defaults
        error_codes = data.get("error_codes", None)
        affected_features = data.get("affected_features", None)
        triggering_actions = data.get("triggering_actions", None)
        D = BugReportData(error_codes=error_codes, affected_features=affected_features, triggering_actions=triggering_actions )

        return D

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON of Bug ralated data: {e}")
        return None
    

def parse_tech_diff(json_string: str):
    try:
        # Parse JSON string into a dictionary
        data = json.loads(json_string)

        # Extract values with safe defaults
        connection_issues = data.get("connection_issues", None)
        performance_issues = data.get("performance_issues", None)
        navigation_difficulties = data.get("navigation_difficultiess", None)
        D = TechnicalDifficultiesData(connection_issues=connection_issues, performance_issues=performance_issues, navigation_difficulties=navigation_difficulties )

        return D

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON of tech difficulties data: {e}")
        return None
    

def parse_feat_req(json_string: Union[str, dict]):
    try:
        # Check if the input is already a dictionary
        if isinstance(json_string, dict):
            data = json_string  # Use the dictionary directly
        else:
            # Parse JSON string into a dictionary
            data = json.loads(json_string)
        
        print('Parsed JSON into a dictionary:', data)
        print('HMD AALINAAA')

        # Extract values with safe defaults
        feature_name = data.get("feature_name", None)
        urgency = data.get("urgency", None)
        benefits = data.get("benefits", None)

        # Create and return a FeatureRequestData instance
        return FeatureRequestData(feature_name=feature_name, urgency=urgency, benefits=benefits)
    
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return FeatureRequestData(feature_name=None, urgency=None, benefits=None)

    
# Final suport request processing function
def process_support_request(support_request: SupportRequest) -> ResultRequest:
    
    category = categorize_request(support_request.text) 

    summary = generate_summary(support_request.text)

    extracted_data = None
    if category == Category.BUG:
        extracted_data = parse_bug_report(get_cohere_response(promptDataBug + support_request.text))
    elif category == Category.FEAT:
        extracted_data = parse_feat_req(transform_to_json(get_cohere_response(promptDataFeat + support_request.text)))
    elif category == Category.TECH:
        extracted_data = parse_tech_diff(get_cohere_response(promptDataTech + support_request.text))


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

