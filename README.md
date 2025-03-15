# Project Overview

In this assignment, I built a simplified version of an automation tool that processes  
incoming technical support requests for a platform (Don't mind the random contexts, but there is a theme, and all requests are related to a technical problem with the platform), simulated as text inputs, and returns structured, actionable responses.

---

# Use of Every File

- **requirements.txt:** Contains all dependencies used in the project along with versions.  
  *Note: All installations were done in the terminal, but explicitly in Gen.ipynb.*

- **README.ipynb:** Contains information about project setup, design, and constitutes a walkthrough of the workflow.
- **main.py:** Source code.
- **test.py:** Used for troubleshooting and testing purposes before moving on to FastAPI-Swagger UI.
- **Gen.ipynb:** Contains code experiments and tests before copying the working code to main.py, as the notebook interface is more comfortable for the developer.
- **.env:** *(Not pushed to Github)* Contains the Cohere API key. You can generate your own [here](https://dashboard.cohere.com/api-keys).
- **README.md:** Although preferred for Notebook markdowns, this file is now redundant.

---

# Setting Up the Project

- **IDE:** Visual Studio Code
- **Dependencies:**  
  Install all dependencies using a PowerShell terminal in VS Code.  
  All dependency versions are listed in **requirements.txt**.
- **Uvicorn:**  
  Ensure you use uvicorn (install it via PowerShell) for FastAPI. It guarantees fast performance by automatically restarting the app every time you save (Ctrl+S).

---

# Test Out the App

Use FastAPI-Swagger UI to simulate communications and test the POST endpoint:  
[http://127.0.0.1:8000/docs#/default/create_support_request_support_request__post](http://127.0.0.1:8000/docs#/default/create_support_request_support_request__post)

The POST endpoint worked well during testing.

---

# Design Decisions

I wanted to structure the data as much as possible because having the LLM structure the data for you isn't always guaranteed:

- **Input:**  
  *SupportRequest* entity containing an `id` (int) and other string fields (name, organization, and text, which constitutes the most important part of the input—i.e., the technical request).
  
- **Output:**  
  *ResultRequest* entity that contains:
  - **category:** of type *Category* (the request could be a bug report, a new feature request, a technical difficulty, or a mix—miscellaneous).
  - **Summary:** A short description of the request.
  - **Extracted Data:**  
    Its structure and content depend on the category of the request. It could be of type `None` or one of the four other types, each corresponding to a category.

---

# Logic & Architecture

The **Gen.ipynb** file better depicts the envisioned interactions between entities and explains the functionality of each function.  
*Note: It is recommended to refer to Gen.ipynb for a clearer picture than what main.py provides.*

---

**Happy coding!**
