import requests

#to be sent in the POST request
new_support_request = {
    "id": 3,
    "name": "Leonardo Dicaprio",
    "organization": "Warner Bros",
    "text": "I need help with my account, I keep having difficulties logging in to it"
}

#Abaath ya Walid
response = requests.post("http://127.0.0.1:8000/support_request/", json=new_support_request)

print(response.json())
