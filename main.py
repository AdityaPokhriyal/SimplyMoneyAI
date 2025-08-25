from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from pymongo import MongoClient
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
import os

# Initialize Gemini client
client = genai.Client(api_key="AIzaSyAiECjwRWdaP51XGzVDZ_lcfoeyczw4NKE")

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["gold_investments"]
transactions = db["transactions"]

app = FastAPI()

# Mount static folder for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return JSONResponse({"error": "No prompt provided"}, status_code=400)

    lower = prompt.lower()
    is_gold_investment = ("gold" in lower and "invest" in lower) or "gold investment" in lower

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[{"text": prompt}],
    )

    gemini_answer = "".join(
        [c.text for c in response.candidates[0].content.parts if hasattr(c, "text")]
    )

    if is_gold_investment:
        gemini_answer += "\n\n👉 Would you like to buy digital gold? Click the button below to start."

    return JSONResponse({"response": gemini_answer, "gold_offer": is_gold_investment})

@app.post("/buy-gold")
async def buy_gold(request: Request):
    data = await request.json()
    user_info = data.get("user_info", {})
    investment = data.get("investment", {})

    # Calculate gold quantity
    inr = float(investment.get("amount_inr", 0))
    gold_price_per_gram = 10000
    grams = inr / gold_price_per_gram

    # Store in DB
    transaction = {
        "user": user_info,
        "investment": {
            "amount_inr": inr,
            "grams": grams
        },
        "status": "success"
    }
    result = transactions.insert_one(transaction)

    # Add inserted ID as string
    transaction["_id"] = str(result.inserted_id)

    return JSONResponse(content=jsonable_encoder({
        "message": "Transaction successful!",
        "details": transaction
    }))
