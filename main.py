from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

# MongoDB client setup
client = MongoClient("mongodb://localhost:27017")  # Update with your MongoDB Atlas/local URI
db = client["vodex_db"]  # Replace with your database name

app = FastAPI()

# Pydantic models for Items and Clock-In Records
class Item(BaseModel):
    name: str
    email: EmailStr
    item_name: str
    quantity: int
    expiry_date: datetime

class ClockInRecord(BaseModel):
    email: EmailStr
    location: str

# Helper function for items
def item_helper(item) -> dict:
    return {
        "id": str(item["_id"]),
        "name": item["name"],
        "email": item["email"],
        "item_name": item["item_name"],
        "quantity": item["quantity"],
        "expiry_date": item["expiry_date"],
        "insert_date": item["insert_date"]
    }

# Helper function for clock-in records
def clock_in_helper(record) -> dict:
    return {
        "id": str(record["_id"]),
        "email": record["email"],
        "location": record["location"],
        "insert_datetime": record["insert_datetime"]
    }

# Items API
@app.post("/items", response_model=Item,
          responses={
              200: {
                  "description": "Successful Response",
                  "content": {
                      "application/json": {
                          "example": {
                              "name": "string",
                              "email": "user@example.com",
                              "item_name": "string",
                              "quantity": 0,
                              "expiry_date": "2024-10-12T05:32:24.935Z",
                              "insert_date": "2024-10-12T05:32:24.935Z"
                          }
                      }
                  }
              }
          })
async def create_item(item: Item):
    item_dict = item.dict()
    item_dict["insert_date"] = datetime.now().isoformat()
    result = db.items.insert_one(item_dict)
    return {**item_dict, "id": str(result.inserted_id)}

@app.get("/items/{id}", response_model=Item)
async def read_item(id: str):
    item = db.items.find_one({"_id": ObjectId(id)})
    if item:
        return item_helper(item)
    raise HTTPException(status_code=404, detail="Item not found")

@app.get("/items/filter", response_model=List[Item])
async def filter_items(email: Optional[str] = None, expiry_date: Optional[str] = None,
                       insert_date: Optional[str] = None, quantity: Optional[int] = None):
    query = {}
    if email:
        query["email"] = email
    if expiry_date:
        query["expiry_date"] = {"$gt": expiry_date}
    if insert_date:
        query["insert_date"] = {"$gt": insert_date}
    if quantity is not None:
        query["quantity"] = {"$gte": quantity}

    items = list(db.items.find(query))
    return [item_helper(item) for item in items]

@app.delete("/items/{id}")
async def delete_item(id: str):
    result = db.items.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return {"detail": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{id}", response_model=Item)
async def update_item(id: str, item: Item):
    result = db.items.update_one({"_id": ObjectId(id)}, {"$set": item.dict(exclude={"insert_date"})})
    if result.modified_count == 1:
        updated_item = db.items.find_one({"_id": ObjectId(id)})
        return item_helper(updated_item)
    raise HTTPException(status_code=404, detail="Item not found")

# Aggregation API for counting items by email
@app.get("/items/aggregation")
async def aggregate_items_by_email():
    pipeline = [
        {"$group": {"_id": "$email", "count": {"$sum": 1}}}
    ]
    result = list(db.items.aggregate(pipeline))
    return result

# Clock-In Records API
@app.post("/clock-in", response_model=ClockInRecord)
async def create_clock_in(clock_in: ClockInRecord):
    clock_in_dict = clock_in.dict()
    clock_in_dict["insert_datetime"] = datetime.now().isoformat()
    result = db.clock_in.insert_one(clock_in_dict)
    return {**clock_in_dict, "id": str(result.inserted_id)}

@app.get("/clock-in/{id}", response_model=ClockInRecord)
async def read_clock_in(id: str):
    clock_in = db.clock_in.find_one({"_id": ObjectId(id)})
    if clock_in:
        return clock_in_helper(clock_in)
    raise HTTPException(status_code=404, detail="Clock-in record not found")

@app.get("/clock-in/filter", response_model=List[ClockInRecord])
async def filter_clock_ins(email: Optional[str] = None, location: Optional[str] = None,
                           insert_datetime: Optional[str] = None):
    query = {}
    if email:
        query["email"] = email
    if location:
        query["location"] = location
    if insert_datetime:
        query["insert_datetime"] = {"$gt": insert_datetime}

    clock_ins = list(db.clock_in.find(query))
    return [clock_in_helper(record) for record in clock_ins]

@app.delete("/clock-in/{id}")
async def delete_clock_in(id: str):
    result = db.clock_in.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return {"detail": "Clock-in record deleted"}
    raise HTTPException(status_code=404, detail="Clock-in record not found")

@app.put("/clock-in/{id}", response_model=ClockInRecord)
async def update_clock_in(id: str, clock_in: ClockInRecord):
    result = db.clock_in.update_one({"_id": ObjectId(id)}, {"$set": clock_in.dict(exclude={"insert_datetime"})})
    if result.modified_count == 1:
        updated_clock_in = db.clock_in.find_one({"_id": ObjectId(id)})
        return clock_in_helper(updated_clock_in)
    raise HTTPException(status_code=404, detail="Clock-in record not found")
