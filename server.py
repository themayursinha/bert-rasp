from fastapi import FastAPI, APIRouter, HTTPException, Depends
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from starlette.requests import Request

app = FastAPI()
api_router = APIRouter()

# Load model and tokenizer at startup
tokenizer = AutoTokenizer.from_pretrained("b1nch3f/owasp-bert")
model = AutoModelForSequenceClassification.from_pretrained("b1nch3f/owasp-bert")
model.eval()


# Pydantic model for request data
class Data(BaseModel):
    params: dict


# Function to check if payload is malicious
async def check_payload(request: Request):
    if request.method == "POST":
        payload = await request.json()
        result_string = ' '.join(f'{key} {value}' for key, value in payload.items())

        inputs = tokenizer(result_string, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
        
        logits = outputs.logits
        prediction = torch.argmax(logits, dim=-1).item()

        if prediction == 1:
            raise HTTPException(status_code=400, detail={"message": "Malicious payload detected"})
        elif prediction == 0:
            return {"message": "Normal payload detected"}


@api_router.post("/userLogin")
async def user_login(data: Data, payload_status: dict = Depends(check_payload)):
    # Process user login
    return {"message": "User login successful"}


# Include the router in the app
app.include_router(api_router, prefix="/api")