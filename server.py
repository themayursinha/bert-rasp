import asyncio
from starlette.requests import Request
from starlette.responses import Response
from typing import Any
from fastapi import Depends, FastAPI, Form, APIRouter, HTTPException, Request
from starlette.responses import JSONResponse
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("b1nch3f/owasp-bert")
model = AutoModelForSequenceClassification.from_pretrained("b1nch3f/owasp-bert")

app = FastAPI()
api_router = APIRouter()


# Define a Pydantic model to represent the expected request body
class Data(BaseModel):
    params: Any


async def payload_inspector(request: Request):
    is_malicious = None
    is_normal = None

    if request.method == "POST":
        payload = await request.json()
        # print(payload)

        result_string = ' '.join(f'{key} {value}' for key, value in payload.items())

        input_data = tokenizer(result_string)

        model.eval()

        # Convert the input into PyTorch tensors
        input_ids = torch.tensor([input_data['input_ids']])
        token_type_ids = torch.tensor([input_data['token_type_ids']])
        attention_mask = torch.tensor([input_data['attention_mask']])

        # Perform inference
        with torch.no_grad():
            outputs = model(input_ids=input_ids, token_type_ids=token_type_ids, attention_mask=attention_mask)

        logits = outputs.logits

        prediction = torch.argmax(logits, dim=-1)

        if prediction[0].item() == 1:
            is_malicious = True
            is_normal = False
        elif prediction[0].item() == 0:
            is_malicious = False
            is_normal = True

    if is_malicious and not is_normal:
        custom_message = {"message": "Malicious payload detected"}
        raise HTTPException(status_code=400, detail=custom_message)
    elif is_normal and not is_malicious:
        custom_message = {"message": "Normal payload detected"}
        raise HTTPException(status_code=200, detail=custom_message)


@api_router.post("/userLogin")
async def user_login(data: Data):
    return {"message": "Hello World"}


# the trick here is including log_json in the dependencies:
app.include_router(api_router, prefix="/api", dependencies=[Depends(payload_inspector)])