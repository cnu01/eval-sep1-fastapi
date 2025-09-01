MONGO_URI = "mongodb+srv://cnu:jb1y6avC2cm6oRxg@cluster0.xiuz0db.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB = 'wallet_db'

from fastapi import FastAPI, Http
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from datetime import datetime




app = FastAPI(title="Digital Wallet", version="1.0.0")

try:
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB]
    print("Connected to MongoDB")
    

except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)
    
users = db["users"]
transactions = db["transactions"]


class User(BaseModel):
    _id: str
    username: str
    email: str
    balance: float
    password: str
    phone_number: str
    created_at: datetime
    updated_at: datetime

class Transaction(BaseModel):
  _id: str
  user_id: str
  transaction_type: str
  amount: float
  description: str
  reference_transaction_id: str
  recipient_user_id: str
  created_at: datetime
  updated_at: datetime


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Digital Wallet API"}


@app.post("/users/", response_model=User)
async def create_user(user: User):
    user.created_at = datetime.now()
    user.updated_at = datetime.now()
    result = await users.insert_one(user.dict())
    user._id = str(result.inserted_id)
    return user