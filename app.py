MONGO_URI = "mongodb+srv://cnu:jb1y6avC2cm6oRxg@cluster0.xiuz0db.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB = 'wallet_db'

from random import Random
from fastapi import FastAPI , HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Digital Wallet", version="1.0.0")

app.add_middleware(
    CORSMiddleware, # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
#   transaction_type: "CREDIT" | "DEBIT" | "TRANSFER_IN" | "TRANSFER_OUT"
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

# User Profile Endpoints

@app.post("/users/create")
async def create_user(user: User):
   try:
      find_user = await users.find_one({"email": user.email})
      if find_user:
          return HTTPException(status_code=400, detail="User already exists")
      user_dict = user.dict()
      user_dict["created_at"] = datetime.now()
      user_dict["updated_at"] = datetime.now()
      result = await users.insert_one(user_dict)
    #   user._id = str(result.inserted_id)
      userDetails = await users.find_one({"_id": result.inserted_id})
      userDetails['_id'] = str(userDetails['_id'])
      return {"message": "User created successfully", "user": userDetails}
   except Exception as e:
       print(f"Error creating user: {e}")
       return HTTPException(status_code=500, detail="Error creating user")


@app.get("/users/{user_id}")
async def read_user(user_id: str):
    user = await users.find_one({"_id": ObjectId(user_id)})
    if user:
        user['_id'] = str(user['_id'])
        return user
    return HTTPException(status_code=404, detail="User not found")


@app.put("/users/{user_id}")
async def update_user(user_id: str, user: User):
    user_dict = user.dict()
    user_dict.pop("_id", None)
    result = await users.update_one({"_id": ObjectId(user_id)}, {"$set": user_dict})
    if result.modified_count == 1:
        user._id = user_id
        return {"message": "User updated successfully", "user": user}
    return HTTPException(status_code=404, detail="User not found")


# Wallet Endpoints

@app.get('/wallet/{user_id}/balance')
async def get_wallet_balance(user_id: str):
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
        if user:
            return {'user_id':user_id,"balance": user['balance'], "last_updated": user['updated_at']}
        return HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        print(f"Error getting wallet balance: {e}")
        return HTTPException(status_code=500, detail="Error getting wallet balance")


@app.post('/wallet/{user_id}/add-money')
async def deposit_funds(user_id: str, amount: float, description: str = None):
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return HTTPException(status_code=404, detail="User not found")
        
        new_balance = user['balance'] + amount
        await users.update_one({"_id": ObjectId(user_id)}, {"$set": {"balance": new_balance, "updated_at": datetime.now()}})
        reference_transaction_id = Random().random()


        transaction = Transaction(
            user_id=user_id,
            transaction_type="CREDIT",
            amount=amount,
            description=description,
            reference_transaction_id= str(reference_transaction_id),
            recipient_user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = await transactions.insert_one(transaction.dict())
        transaction._id = str(result.inserted_id)
        
        return {"message": "Deposit successful", "transaction": transaction}
    except Exception as e:
        print(f"Error depositing funds: {e}")
        return HTTPException(status_code=500, detail="Error depositing funds")


@app.post('/wallet/{user_id}/withdraw-money')
async def withdraw_funds(user_id: str, amount: float, description: str = None):
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return HTTPException(status_code=404, detail="User not found")

        new_balance = user['balance'] - amount
        print(new_balance)
        if new_balance <= 0 or 0.0:
            return HTTPException(status_code=400, detail="Insufficient funds")

        await users.update_one({"_id": ObjectId(user_id)}, {"$set": {"balance": new_balance, "updated_at": datetime.now()}})
        reference_transaction_id = Random().random()
        reference_transaction_id = str(reference_transaction_id)

        transaction = Transaction(
            user_id=user_id,
            transaction_type="DEBIT",
            amount=amount,
            description=description,
            reference_transaction_id=reference_transaction_id,
            recipient_user_id=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = await transactions.insert_one(transaction.dict())
        transaction._id = str(result.inserted_id)

        return {"message": "Withdrawal successful", "transaction": transaction}
    except Exception as e:
        print(f"Error withdrawing funds: {e}")
        return HTTPException(status_code=500, detail="Error withdrawing funds")
    

# Transaction Endpoints
@app.get('/wallet/{user_id}/transactions')
async def get_transaction_history(user_id: str, page: int = 1, page_size: int = 10):
    try:
        user = await users.find_one({"_id": ObjectId(user_id)})
        if not user:
            return HTTPException(status_code=404, detail="User not found")

        skip = (page - 1) * page_size
        cursor = transactions.find({"user_id": user_id}).skip(skip).limit(page_size)
        transaction_list = []
        async for transaction in cursor:
            transaction['_id'] = str(transaction['_id'])
            transaction_list.append(transaction)

        return {"transactions": transaction_list, "page": page, "page_size": page_size, "total": len(transaction_list)}
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return HTTPException(status_code=500, detail="Error fetching transactions")


@app.get('/transactions/detail/{transaction_id}')
async def get_transaction_detail(transaction_id: str):
    try:
        transaction = await transactions.find_one({"_id": ObjectId(transaction_id)})
        if not transaction:
            return HTTPException(status_code=404, detail="Transaction not found")
        transaction['_id'] = str(transaction['_id'])
        return Transaction(**transaction)
    except Exception as e:
        print(f"Error fetching transaction detail: {e}")
        return HTTPException(status_code=500, detail="Error fetching transaction detail")
    
    
# Transfer Endpoints

@app.post('/transfer')
async def transfer_funds(sender_user_id: str, recipient_user_id: str, amount: float, description: str = None):
    try:
        sender = await users.find_one({"_id": ObjectId(sender_user_id)})
        recipient = await users.find_one({"_id": ObjectId(recipient_user_id)})

        if not sender or not recipient:
            return HTTPException(status_code=404, detail="Sender or recipient not found")

        if sender['balance'] < amount:
            return HTTPException(status_code=400, detail="Insufficient funds")

        new_sender_balance = sender['balance'] - amount
        new_recipient_balance = recipient['balance'] + amount

        await users.update_one({"_id": ObjectId(sender_user_id)}, {"$set": {"balance": new_sender_balance, "updated_at": datetime.now()}})
        await users.update_one({"_id": ObjectId(recipient_user_id)}, {"$set": {"balance": new_recipient_balance, "updated_at": datetime.now()}})

        reference_transaction_id = Random().random()
        reference_transaction_id = str(reference_transaction_id)

        sender_transaction = Transaction(
            user_id=sender_user_id,
            transaction_type="TRANSFER_OUT",
            amount=amount,
            description=description,
            reference_transaction_id=reference_transaction_id,
            recipient_user_id=recipient_user_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result_sender = await transactions.insert_one(sender_transaction.dict())
        sender_transaction._id = str(result_sender.inserted_id)

        recipient_transaction = Transaction(
            user_id=recipient_user_id,
            transaction_type="TRANSFER_IN",
            amount=amount,
            description=description,
            reference_transaction_id=reference_transaction_id,
            recipient_user_id=recipient_user_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result_recipient = await transactions.insert_one(recipient_transaction.dict())
        recipient_transaction._id = str(result_recipient.inserted_id)

        return {"message": "Transfer successful", "transaction": sender_transaction}
    except Exception as e:
        print(f"Error transferring funds: {e}")
        return HTTPException(status_code=500, detail="Error transferring funds")
    
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
