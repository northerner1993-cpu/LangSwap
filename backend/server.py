from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class LessonItem(BaseModel):
    thai: str
    romanization: str
    english: str
    example: Optional[str] = None

class Lesson(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    title: str
    category: str  # alphabet, numbers, conversations
    subcategory: Optional[str] = None  # consonants, vowels, greetings, etc
    description: str
    items: List[LessonItem]
    order: int = 0
    language_mode: str = "learn-thai"  # "learn-thai" or "learn-english"

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class Progress(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = "default_user"  # For MVP, using default user
    lesson_id: str
    completed: bool = False
    completed_items: List[int] = []  # indices of completed items
    last_accessed: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

class Favorite(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = "default_user"
    lesson_id: str
    item_index: int
    item_data: LessonItem
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Thai Language Learning API"}

@api_router.get("/lessons", response_model=List[Lesson])
async def get_all_lessons(category: Optional[str] = None):
    query = {}
    if category:
        query["category"] = category
    
    lessons = await db.lessons.find(query).sort("order", 1).to_list(1000)
    for lesson in lessons:
        lesson["_id"] = str(lesson["_id"])
    return lessons

@api_router.get("/lessons/{lesson_id}", response_model=Lesson)
async def get_lesson(lesson_id: str):
    try:
        lesson = await db.lessons.find_one({"_id": ObjectId(lesson_id)})
        if lesson:
            lesson["_id"] = str(lesson["_id"])
            return lesson
        raise HTTPException(status_code=404, detail="Lesson not found")
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/progress")
async def save_progress(progress: Progress):
    progress_dict = progress.dict(by_alias=True, exclude={"id"})
    progress_dict["last_accessed"] = datetime.utcnow()
    
    # Upsert progress
    result = await db.progress.update_one(
        {"user_id": progress.user_id, "lesson_id": progress.lesson_id},
        {"$set": progress_dict},
        upsert=True
    )
    return {"success": True, "modified": result.modified_count}

@api_router.get("/progress")
async def get_progress(user_id: str = "default_user"):
    progress_list = await db.progress.find({"user_id": user_id}).to_list(1000)
    for p in progress_list:
        p["_id"] = str(p["_id"])
    return progress_list

@api_router.post("/favorites")
async def toggle_favorite(favorite: Favorite):
    # Check if already exists
    existing = await db.favorites.find_one({
        "user_id": favorite.user_id,
        "lesson_id": favorite.lesson_id,
        "item_index": favorite.item_index
    })
    
    if existing:
        # Remove favorite
        await db.favorites.delete_one({"_id": existing["_id"]})
        return {"success": True, "action": "removed"}
    else:
        # Add favorite
        fav_dict = favorite.dict(by_alias=True, exclude={"id"})
        result = await db.favorites.insert_one(fav_dict)
        return {"success": True, "action": "added", "id": str(result.inserted_id)}

@api_router.get("/favorites")
async def get_favorites(user_id: str = "default_user"):
    favorites = await db.favorites.find({"user_id": user_id}).sort("created_at", -1).to_list(1000)
    for f in favorites:
        f["_id"] = str(f["_id"])
    return favorites

@api_router.post("/clear-data")
async def clear_data():
    """Clear all lessons data"""
    await db.lessons.delete_many({})
    await db.progress.delete_many({})
    await db.favorites.delete_many({})
    return {"message": "All data cleared"}

@api_router.post("/init-data")
async def initialize_data(force: bool = False):
    """Initialize database with Thai learning content"""
    # Check if data already exists
    count = await db.lessons.count_documents({})
    if count > 0 and not force:
        return {"message": "Data already initialized", "count": count}
    
    # Thai Consonants
    consonants_data = [
        {"thai": "ก", "romanization": "k", "english": "Kor Kai (chicken)", "example": "กา (crow)"},
        {"thai": "ข", "romanization": "kh", "english": "Khor Khai (egg)", "example": "ขาว (white)"},
        {"thai": "ฃ", "romanization": "kh", "english": "Khor Khuat (bottle)", "example": "obsolete"},
        {"thai": "ค", "romanization": "kh", "english": "Khor Khwai (buffalo)", "example": "ควาย (buffalo)"},
        {"thai": "ฅ", "romanization": "kh", "english": "Khor Khon (person)", "example": "obsolete"},
        {"thai": "ฆ", "romanization": "kh", "english": "Khor Rakhang (bell)", "example": "ระฆัง (bell)"},
        {"thai": "ง", "romanization": "ng", "english": "Ngor Nguu (snake)", "example": "งู (snake)"},
        {"thai": "จ", "romanization": "j", "english": "Jor Jaan (plate)", "example": "จาน (plate)"},
        {"thai": "ฉ", "romanization": "ch", "english": "Chor Ching (cymbal)", "example": "ฉิ่ง (cymbal)"},
        {"thai": "ช", "romanization": "ch", "english": "Chor Chang (elephant)", "example": "ช้าง (elephant)"},
        {"thai": "ซ", "romanization": "s", "english": "Sor So (chain)", "example": "โซ่ (chain)"},
        {"thai": "ฌ", "romanization": "ch", "english": "Chor Choe (tree)", "example": "เฌอ (tree)"},
        {"thai": "ญ", "romanization": "y", "english": "Yor Ying (woman)", "example": "หญิง (woman)"},
        {"thai": "ฎ", "romanization": "d", "english": "Dor Chada (headdress)", "example": "ชฎา (headdress)"},
        {"thai": "ฏ", "romanization": "t", "english": "Tor Patak (goad)", "example": "ปฏัก (goad)"},
        {"thai": "ฐ", "romanization": "th", "english": "Thor Thaan (base)", "example": "ฐาน (base)"},
        {"thai": "ฑ", "romanization": "th", "english": "Thor Montho (Montho)", "example": "มณโฑ (Montho)"},
        {"thai": "ฒ", "romanization": "th", "english": "Thor Phuthao (elder)", "example": "ผู้เฒ่า (elder)"},
        {"thai": "ณ", "romanization": "n", "english": "Nor Neen (novice)", "example": "เณร (novice)"},
        {"thai": "ด", "romanization": "d", "english": "Dor Dek (child)", "example": "เด็ก (child)"},
        {"thai": "ต", "romanization": "t", "english": "Tor Tao (turtle)", "example": "เต่า (turtle)"},
        {"thai": "ถ", "romanization": "th", "english": "Thor Thung (bag)", "example": "ถุง (bag)"},
        {"thai": "ท", "romanization": "th", "english": "Thor Thahan (soldier)", "example": "ทหาร (soldier)"},
        {"thai": "ธ", "romanization": "th", "english": "Thor Thong (flag)", "example": "ธง (flag)"},
        {"thai": "น", "romanization": "n", "english": "Nor Nuu (mouse)", "example": "หนู (mouse)"},
        {"thai": "บ", "romanization": "b", "english": "Bor Baimai (leaf)", "example": "ใบไม้ (leaf)"},
        {"thai": "ป", "romanization": "p", "english": "Por Plaa (fish)", "example": "ปลา (fish)"},
        {"thai": "ผ", "romanization": "ph", "english": "Phor Phueng (bee)", "example": "ผึ้ง (bee)"},
        {"thai": "ฝ", "romanization": "f", "english": "For Faa (lid)", "example": "ฝา (lid)"},
        {"thai": "พ", "romanization": "ph", "english": "Phor Phaan (tray)", "example": "พาน (tray)"},
        {"thai": "ฟ", "romanization": "f", "english": "For Fan (teeth)", "example": "ฟัน (teeth)"},
        {"thai": "ภ", "romanization": "ph", "english": "Phor Samphao (sailboat)", "example": "สำเภา (sailboat)"},
        {"thai": "ม", "romanization": "m", "english": "Mor Maa (horse)", "example": "ม้า (horse)"},
        {"thai": "ย", "romanization": "y", "english": "Yor Yak (giant)", "example": "ยักษ์ (giant)"},
        {"thai": "ร", "romanization": "r", "english": "Ror Ruea (boat)", "example": "เรือ (boat)"},
        {"thai": "ล", "romanization": "l", "english": "Lor Ling (monkey)", "example": "ลิง (monkey)"},
        {"thai": "ว", "romanization": "w", "english": "Wor Waen (ring)", "example": "แหวน (ring)"},
        {"thai": "ศ", "romanization": "s", "english": "Sor Sala (pavilion)", "example": "ศาลา (pavilion)"},
        {"thai": "ษ", "romanization": "s", "english": "Sor Ruesii (hermit)", "example": "ฤๅษี (hermit)"},
        {"thai": "ส", "romanization": "s", "english": "Sor Suea (tiger)", "example": "เสือ (tiger)"},
        {"thai": "ห", "romanization": "h", "english": "Hor Hiip (chest)", "example": "หีบ (chest)"},
        {"thai": "ฬ", "romanization": "l", "english": "Lor Chula (kite)", "example": "จุฬา (kite)"},
        {"thai": "อ", "romanization": "or", "english": "Or Ang (basin)", "example": "อ่าง (basin)"},
        {"thai": "ฮ", "romanization": "h", "english": "Hor Nokhuk (owl)", "example": "นกฮูก (owl)"}
    ]
    
    # Thai Vowels
    vowels_data = [
        {"thai": "–ะ", "romanization": "a", "english": "short 'a'", "example": "กะ (ka)"},
        {"thai": "–า", "romanization": "aa", "english": "long 'aa'", "example": "กา (kaa)"},
        {"thai": "ิ–", "romanization": "i", "english": "short 'i'", "example": "กิ (ki)"},
        {"thai": "ี–", "romanization": "ii", "english": "long 'ii'", "example": "กี (kii)"},
        {"thai": "ึ–", "romanization": "ue", "english": "short 'ue'", "example": "กึ (kue)"},
        {"thai": "ื–", "romanization": "uee", "english": "long 'uee'", "example": "กื (kuee)"},
        {"thai": "ุ–", "romanization": "u", "english": "short 'u'", "example": "กุ (ku)"},
        {"thai": "ู–", "romanization": "uu", "english": "long 'uu'", "example": "กู (kuu)"},
        {"thai": "เ–ะ", "romanization": "e", "english": "short 'e'", "example": "เกะ (ke)"},
        {"thai": "เ–", "romanization": "ee", "english": "long 'ee'", "example": "เก (kee)"},
        {"thai": "แ–ะ", "romanization": "ae", "english": "short 'ae'", "example": "แกะ (kae)"},
        {"thai": "แ–", "romanization": "aae", "english": "long 'aae'", "example": "แก (kaae)"},
        {"thai": "โ–ะ", "romanization": "o", "english": "short 'o'", "example": "โกะ (ko)"},
        {"thai": "โ–", "romanization": "oo", "english": "long 'oo'", "example": "โก (koo)"},
        {"thai": "เ–าะ", "romanization": "or", "english": "short 'or'", "example": "เกาะ (kor)"},
        {"thai": "–อ", "romanization": "oor", "english": "long 'oor'", "example": "กอ (koor)"},
        {"thai": "เ–ียะ", "romanization": "ia", "english": "short 'ia'", "example": "เกียะ (kia)"},
        {"thai": "เ–ีย", "romanization": "iia", "english": "long 'iia'", "example": "เกีย (kiia)"},
        {"thai": "เ–ือะ", "romanization": "uea", "english": "short 'uea'", "example": "เกือะ (kuea)"},
        {"thai": "เ–ือ", "romanization": "ueea", "english": "long 'ueea'", "example": "เกือ (kueea)"},
        {"thai": "–ัวะ", "romanization": "ua", "english": "short 'ua'", "example": "กัวะ (kua)"},
        {"thai": "–ัว", "romanization": "uua", "english": "long 'uua'", "example": "กัว (kuua)"}
    ]
    
    # Numbers 0-100 (complete)
    numbers_basic = [
        {"thai": "ศูนย์", "romanization": "soon", "english": "0", "example": "zero"},
        {"thai": "หนึ่ง", "romanization": "neung", "english": "1", "example": "one"},
        {"thai": "สอง", "romanization": "song", "english": "2", "example": "two"},
        {"thai": "สาม", "romanization": "saam", "english": "3", "example": "three"},
        {"thai": "สี่", "romanization": "sii", "english": "4", "example": "four"},
        {"thai": "ห้า", "romanization": "haa", "english": "5", "example": "five"},
        {"thai": "หก", "romanization": "hok", "english": "6", "example": "six"},
        {"thai": "เจ็ด", "romanization": "jet", "english": "7", "example": "seven"},
        {"thai": "แปด", "romanization": "bpaet", "english": "8", "example": "eight"},
        {"thai": "เก้า", "romanization": "gao", "english": "9", "example": "nine"},
        {"thai": "สิบ", "romanization": "sip", "english": "10", "example": "ten"},
        {"thai": "สิบเอ็ด", "romanization": "sip-et", "english": "11", "example": "eleven"},
        {"thai": "สิบสอง", "romanization": "sip-song", "english": "12", "example": "twelve"},
        {"thai": "สิบสาม", "romanization": "sip-saam", "english": "13", "example": "thirteen"},
        {"thai": "สิบสี่", "romanization": "sip-sii", "english": "14", "example": "fourteen"},
        {"thai": "สิบห้า", "romanization": "sip-haa", "english": "15", "example": "fifteen"},
        {"thai": "สิบหก", "romanization": "sip-hok", "english": "16", "example": "sixteen"},
        {"thai": "สิบเจ็ด", "romanization": "sip-jet", "english": "17", "example": "seventeen"},
        {"thai": "สิบแปด", "romanization": "sip-bpaet", "english": "18", "example": "eighteen"},
        {"thai": "สิบเก้า", "romanization": "sip-gao", "english": "19", "example": "nineteen"},
        {"thai": "ยี่สิบ", "romanization": "yii-sip", "english": "20", "example": "twenty"},
        {"thai": "ยี่สิบเอ็ด", "romanization": "yii-sip-et", "english": "21", "example": "twenty-one"},
        {"thai": "ยี่สิบสอง", "romanization": "yii-sip-song", "english": "22", "example": "twenty-two"},
        {"thai": "ยี่สิบสาม", "romanization": "yii-sip-saam", "english": "23", "example": "twenty-three"},
        {"thai": "ยี่สิบสี่", "romanization": "yii-sip-sii", "english": "24", "example": "twenty-four"},
        {"thai": "ยี่สิบห้า", "romanization": "yii-sip-haa", "english": "25", "example": "twenty-five"},
        {"thai": "ยี่สิบหก", "romanization": "yii-sip-hok", "english": "26", "example": "twenty-six"},
        {"thai": "ยี่สิบเจ็ด", "romanization": "yii-sip-jet", "english": "27", "example": "twenty-seven"},
        {"thai": "ยี่สิบแปด", "romanization": "yii-sip-bpaet", "english": "28", "example": "twenty-eight"},
        {"thai": "ยี่สิบเก้า", "romanization": "yii-sip-gao", "english": "29", "example": "twenty-nine"},
        {"thai": "สามสิบ", "romanization": "saam-sip", "english": "30", "example": "thirty"},
        {"thai": "สามสิบเอ็ด", "romanization": "saam-sip-et", "english": "31", "example": "thirty-one"},
        {"thai": "สามสิบสอง", "romanization": "saam-sip-song", "english": "32", "example": "thirty-two"},
        {"thai": "สามสิบสาม", "romanization": "saam-sip-saam", "english": "33", "example": "thirty-three"},
        {"thai": "สามสิบสี่", "romanization": "saam-sip-sii", "english": "34", "example": "thirty-four"},
        {"thai": "สามสิบห้า", "romanization": "saam-sip-haa", "english": "35", "example": "thirty-five"},
        {"thai": "สามสิบหก", "romanization": "saam-sip-hok", "english": "36", "example": "thirty-six"},
        {"thai": "สามสิบเจ็ด", "romanization": "saam-sip-jet", "english": "37", "example": "thirty-seven"},
        {"thai": "สามสิบแปด", "romanization": "saam-sip-bpaet", "english": "38", "example": "thirty-eight"},
        {"thai": "สามสิบเก้า", "romanization": "saam-sip-gao", "english": "39", "example": "thirty-nine"},
        {"thai": "สี่สิบ", "romanization": "sii-sip", "english": "40", "example": "forty"},
        {"thai": "สี่สิบเอ็ด", "romanization": "sii-sip-et", "english": "41", "example": "forty-one"},
        {"thai": "สี่สิบสอง", "romanization": "sii-sip-song", "english": "42", "example": "forty-two"},
        {"thai": "สี่สิบสาม", "romanization": "sii-sip-saam", "english": "43", "example": "forty-three"},
        {"thai": "สี่สิบสี่", "romanization": "sii-sip-sii", "english": "44", "example": "forty-four"},
        {"thai": "สี่สิบห้า", "romanization": "sii-sip-haa", "english": "45", "example": "forty-five"},
        {"thai": "สี่สิบหก", "romanization": "sii-sip-hok", "english": "46", "example": "forty-six"},
        {"thai": "สี่สิบเจ็ด", "romanization": "sii-sip-jet", "english": "47", "example": "forty-seven"},
        {"thai": "สี่สิบแปด", "romanization": "sii-sip-bpaet", "english": "48", "example": "forty-eight"},
        {"thai": "สี่สิบเก้า", "romanization": "sii-sip-gao", "english": "49", "example": "forty-nine"},
        {"thai": "ห้าสิบ", "romanization": "haa-sip", "english": "50", "example": "fifty"},
        {"thai": "ห้าสิบเอ็ด", "romanization": "haa-sip-et", "english": "51", "example": "fifty-one"},
        {"thai": "ห้าสิบสอง", "romanization": "haa-sip-song", "english": "52", "example": "fifty-two"},
        {"thai": "ห้าสิบสาม", "romanization": "haa-sip-saam", "english": "53", "example": "fifty-three"},
        {"thai": "ห้าสิบสี่", "romanization": "haa-sip-sii", "english": "54", "example": "fifty-four"},
        {"thai": "ห้าสิบห้า", "romanization": "haa-sip-haa", "english": "55", "example": "fifty-five"},
        {"thai": "ห้าสิบหก", "romanization": "haa-sip-hok", "english": "56", "example": "fifty-six"},
        {"thai": "ห้าสิบเจ็ด", "romanization": "haa-sip-jet", "english": "57", "example": "fifty-seven"},
        {"thai": "ห้าสิบแปด", "romanization": "haa-sip-bpaet", "english": "58", "example": "fifty-eight"},
        {"thai": "ห้าสิบเก้า", "romanization": "haa-sip-gao", "english": "59", "example": "fifty-nine"},
        {"thai": "หกสิบ", "romanization": "hok-sip", "english": "60", "example": "sixty"},
        {"thai": "หกสิบเอ็ด", "romanization": "hok-sip-et", "english": "61", "example": "sixty-one"},
        {"thai": "หกสิบสอง", "romanization": "hok-sip-song", "english": "62", "example": "sixty-two"},
        {"thai": "หกสิบสาม", "romanization": "hok-sip-saam", "english": "63", "example": "sixty-three"},
        {"thai": "หกสิบสี่", "romanization": "hok-sip-sii", "english": "64", "example": "sixty-four"},
        {"thai": "หกสิบห้า", "romanization": "hok-sip-haa", "english": "65", "example": "sixty-five"},
        {"thai": "หกสิบหก", "romanization": "hok-sip-hok", "english": "66", "example": "sixty-six"},
        {"thai": "หกสิบเจ็ด", "romanization": "hok-sip-jet", "english": "67", "example": "sixty-seven"},
        {"thai": "หกสิบแปด", "romanization": "hok-sip-bpaet", "english": "68", "example": "sixty-eight"},
        {"thai": "หกสิบเก้า", "romanization": "hok-sip-gao", "english": "69", "example": "sixty-nine"},
        {"thai": "เจ็ดสิบ", "romanization": "jet-sip", "english": "70", "example": "seventy"},
        {"thai": "เจ็ดสิบเอ็ด", "romanization": "jet-sip-et", "english": "71", "example": "seventy-one"},
        {"thai": "เจ็ดสิบสอง", "romanization": "jet-sip-song", "english": "72", "example": "seventy-two"},
        {"thai": "เจ็ดสิบสาม", "romanization": "jet-sip-saam", "english": "73", "example": "seventy-three"},
        {"thai": "เจ็ดสิบสี่", "romanization": "jet-sip-sii", "english": "74", "example": "seventy-four"},
        {"thai": "เจ็ดสิบห้า", "romanization": "jet-sip-haa", "english": "75", "example": "seventy-five"},
        {"thai": "เจ็ดสิบหก", "romanization": "jet-sip-hok", "english": "76", "example": "seventy-six"},
        {"thai": "เจ็ดสิบเจ็ด", "romanization": "jet-sip-jet", "english": "77", "example": "seventy-seven"},
        {"thai": "เจ็ดสิบแปด", "romanization": "jet-sip-bpaet", "english": "78", "example": "seventy-eight"},
        {"thai": "เจ็ดสิบเก้า", "romanization": "jet-sip-gao", "english": "79", "example": "seventy-nine"},
        {"thai": "แปดสิบ", "romanization": "bpaet-sip", "english": "80", "example": "eighty"},
        {"thai": "แปดสิบเอ็ด", "romanization": "bpaet-sip-et", "english": "81", "example": "eighty-one"},
        {"thai": "แปดสิบสอง", "romanization": "bpaet-sip-song", "english": "82", "example": "eighty-two"},
        {"thai": "แปดสิบสาม", "romanization": "bpaet-sip-saam", "english": "83", "example": "eighty-three"},
        {"thai": "แปดสิบสี่", "romanization": "bpaet-sip-sii", "english": "84", "example": "eighty-four"},
        {"thai": "แปดสิบห้า", "romanization": "bpaet-sip-haa", "english": "85", "example": "eighty-five"},
        {"thai": "แปดสิบหก", "romanization": "bpaet-sip-hok", "english": "86", "example": "eighty-six"},
        {"thai": "แปดสิบเจ็ด", "romanization": "bpaet-sip-jet", "english": "87", "example": "eighty-seven"},
        {"thai": "แปดสิบแปด", "romanization": "bpaet-sip-bpaet", "english": "88", "example": "eighty-eight"},
        {"thai": "แปดสิบเก้า", "romanization": "bpaet-sip-gao", "english": "89", "example": "eighty-nine"},
        {"thai": "เก้าสิบ", "romanization": "gao-sip", "english": "90", "example": "ninety"},
        {"thai": "เก้าสิบเอ็ด", "romanization": "gao-sip-et", "english": "91", "example": "ninety-one"},
        {"thai": "เก้าสิบสอง", "romanization": "gao-sip-song", "english": "92", "example": "ninety-two"},
        {"thai": "เก้าสิบสาม", "romanization": "gao-sip-saam", "english": "93", "example": "ninety-three"},
        {"thai": "เก้าสิบสี่", "romanization": "gao-sip-sii", "english": "94", "example": "ninety-four"},
        {"thai": "เก้าสิบห้า", "romanization": "gao-sip-haa", "english": "95", "example": "ninety-five"},
        {"thai": "เก้าสิบหก", "romanization": "gao-sip-hok", "english": "96", "example": "ninety-six"},
        {"thai": "เก้าสิบเจ็ด", "romanization": "gao-sip-jet", "english": "97", "example": "ninety-seven"},
        {"thai": "เก้าสิบแปด", "romanization": "gao-sip-bpaet", "english": "98", "example": "ninety-eight"},
        {"thai": "เก้าสิบเก้า", "romanization": "gao-sip-gao", "english": "99", "example": "ninety-nine"},
        {"thai": "หนึ่งร้อย", "romanization": "neung-roi", "english": "100", "example": "one hundred"}
    ]
    
    # Large Numbers
    numbers_large = [
        {"thai": "สองร้อย", "romanization": "song-roi", "english": "200", "example": "two hundred"},
        {"thai": "สามร้อย", "romanization": "saam-roi", "english": "300", "example": "three hundred"},
        {"thai": "สี่ร้อย", "romanization": "sii-roi", "english": "400", "example": "four hundred"},
        {"thai": "ห้าร้อย", "romanization": "haa-roi", "english": "500", "example": "five hundred"},
        {"thai": "หกร้อย", "romanization": "hok-roi", "english": "600", "example": "six hundred"},
        {"thai": "เจ็ดร้อย", "romanization": "jet-roi", "english": "700", "example": "seven hundred"},
        {"thai": "แปดร้อย", "romanization": "bpaet-roi", "english": "800", "example": "eight hundred"},
        {"thai": "เก้าร้อย", "romanization": "gao-roi", "english": "900", "example": "nine hundred"},
        {"thai": "หนึ่งพัน", "romanization": "neung-phan", "english": "1,000", "example": "one thousand"},
        {"thai": "สองพัน", "romanization": "song-phan", "english": "2,000", "example": "two thousand"},
        {"thai": "สามพัน", "romanization": "saam-phan", "english": "3,000", "example": "three thousand"},
        {"thai": "สี่พัน", "romanization": "sii-phan", "english": "4,000", "example": "four thousand"},
        {"thai": "ห้าพัน", "romanization": "haa-phan", "english": "5,000", "example": "five thousand"},
        {"thai": "หนึ่งหมื่น", "romanization": "neung-muen", "english": "10,000", "example": "ten thousand"},
        {"thai": "สองหมื่น", "romanization": "song-muen", "english": "20,000", "example": "twenty thousand"},
        {"thai": "ห้าหมื่น", "romanization": "haa-muen", "english": "50,000", "example": "fifty thousand"},
        {"thai": "หนึ่งแสน", "romanization": "neung-saen", "english": "100,000", "example": "one hundred thousand"},
        {"thai": "สองแสน", "romanization": "song-saen", "english": "200,000", "example": "two hundred thousand"},
        {"thai": "ห้าแสน", "romanization": "haa-saen", "english": "500,000", "example": "five hundred thousand"},
        {"thai": "หนึ่งล้าน", "romanization": "neung-laan", "english": "1,000,000", "example": "one million"}
    ]
    
    # Greetings (Expanded - Easy to Intermediate)
    greetings_data = [
        # Easy Level
        {"thai": "สวัสดี", "romanization": "sawatdee", "english": "Hello / Goodbye", "example": "สวัสดีครับ (male) / สวัสดีค่ะ (female)"},
        {"thai": "สบายดีไหม", "romanization": "sabai dee mai", "english": "How are you?", "example": "คุณสบายดีไหม"},
        {"thai": "สบายดี", "romanization": "sabai dee", "english": "I'm fine", "example": "สบายดีครับ"},
        {"thai": "ขอบคุณ", "romanization": "khob khun", "english": "Thank you", "example": "ขอบคุณมากครับ"},
        {"thai": "ขอบคุณมาก", "romanization": "khob khun maak", "english": "Thank you very much", "example": "ขอบคุณมากค่ะ"},
        {"thai": "ขอโทษ", "romanization": "khor thot", "english": "Sorry / Excuse me", "example": "ขอโทษครับ"},
        {"thai": "ไม่เป็นไร", "romanization": "mai pen rai", "english": "You're welcome / No problem", "example": "ไม่เป็นไรค่ะ"},
        {"thai": "ลาก่อน", "romanization": "laa gorn", "english": "Goodbye", "example": "ลาก่อนค่ะ"},
        {"thai": "แล้วพบกันใหม่", "romanization": "laew phob gan mai", "english": "See you again", "example": "แล้วพบกันใหม่นะ"},
        {"thai": "ราตรีสวัสดิ์", "romanization": "raat-rii sawat", "english": "Good night", "example": "ราตรีสวัสดิ์ครับ"},
        # Intermediate Level
        {"thai": "ยินดีที่ได้รู้จัก", "romanization": "yin dee tii dai ruu jak", "english": "Nice to meet you", "example": "ยินดีที่ได้รู้จักครับ"},
        {"thai": "ยินดีต้อนรับ", "romanization": "yin dee torn rap", "english": "Welcome", "example": "ยินดีต้อนรับสู่ประเทศไทย"},
        {"thai": "ฉันชื่อ...", "romanization": "chan chuu...", "english": "My name is...", "example": "ฉันชื่อจอห์น"},
        {"thai": "คุณชื่ออะไร", "romanization": "khun chuu arai", "english": "What is your name?", "example": "คุณชื่ออะไรครับ"},
        {"thai": "คุณมาจากไหน", "romanization": "khun maa jaak nai", "english": "Where are you from?", "example": "คุณมาจากประเทศอะไร"},
        {"thai": "ฉันมาจาก...", "romanization": "chan maa jaak...", "english": "I'm from...", "example": "ฉันมาจากอเมริกา"},
        {"thai": "ยินดีที่ได้พบคุณ", "romanization": "yin dee tii dai phob khun", "english": "Pleased to meet you", "example": "ยินดีที่ได้พบคุณมาก"},
        {"thai": "เป็นอย่างไรบ้าง", "romanization": "pen yaang rai baang", "english": "How is everything?", "example": "วันนี้เป็นอย่างไรบ้าง"},
        {"thai": "ดีใจที่เจอกัน", "romanization": "dee jai tii jer gan", "english": "Happy to see you", "example": "ดีใจที่เจอกันอีกครั้ง"},
        {"thai": "คิดถึง", "romanization": "khit thueng", "english": "Miss you", "example": "คิดถึงมากเลย"},
    ]
    
    # Common Phrases
    common_phrases_data = [
        {"thai": "ใช่", "romanization": "chai", "english": "Yes", "example": "ใช่ครับ"},
        {"thai": "ไม่ใช่", "romanization": "mai chai", "english": "No", "example": "ไม่ใช่ค่ะ"},
        {"thai": "ไม่รู้", "romanization": "mai ruu", "english": "I don't know", "example": "ไม่รู้ครับ"},
        {"thai": "เข้าใจ", "romanization": "khao jai", "english": "I understand", "example": "ฉันเข้าใจ"},
        {"thai": "ไม่เข้าใจ", "romanization": "mai khao jai", "english": "I don't understand", "example": "ไม่เข้าใจค่ะ"},
        {"thai": "พูดช้าๆ หน่อย", "romanization": "phuut chaa chaa noi", "english": "Speak slowly please", "example": "พูดช้าๆ หน่อยได้ไหม"},
        {"thai": "ช่วยด้วย", "romanization": "chuay duay", "english": "Help!", "example": "ช่วยด้วยครับ"},
        {"thai": "ห้องน้ำอยู่ไหน", "romanization": "hong naam yuu nai", "english": "Where is the bathroom?", "example": "ห้องน้ำอยู่ไหนครับ"},
        {"thai": "ราคาเท่าไหร่", "romanization": "raa-khaa thao rai", "english": "How much?", "example": "อันนี้ราคาเท่าไหร่"},
        {"thai": "แพงไป", "romanization": "phaeng pai", "english": "Too expensive", "example": "แพงไปครับ"},
    ]
    
    # Dining Phrases
    dining_data = [
        {"thai": "อร่อย", "romanization": "aroi", "english": "Delicious", "example": "อาหารอร่อยมาก"},
        {"thai": "หิว", "romanization": "hiw", "english": "Hungry", "example": "ฉันหิว"},
        {"thai": "กระหายน้ำ", "romanization": "gra-haai naam", "english": "Thirsty", "example": "กระหายน้ำมาก"},
        {"thai": "น้ำ", "romanization": "naam", "english": "Water", "example": "ขอน้ำหนึ่งแก้ว"},
        {"thai": "ข้าว", "romanization": "khao", "english": "Rice / Food", "example": "กินข้าวยัง (Have you eaten?)"},
        {"thai": "เผ็ด", "romanization": "phet", "english": "Spicy", "example": "เผ็ดไหม"},
        {"thai": "ไม่เผ็ด", "romanization": "mai phet", "english": "Not spicy", "example": "ไม่เอาเผ็ดครับ"},
        {"thai": "เช็คบิล", "romanization": "check bin", "english": "Check please", "example": "ขอเช็คบิลด้วยครับ"},
        {"thai": "มังสวิรัติ", "romanization": "mang-sa-wi-rat", "english": "Vegetarian", "example": "ฉันกินมังสวิรัติ"},
        {"thai": "อิ่มแล้ว", "romanization": "im laew", "english": "I'm full", "example": "อิ่มแล้วครับ"},
    ]
    
    # Travel Phrases
    travel_data = [
        {"thai": "ไปไหน", "romanization": "pai nai", "english": "Where to go?", "example": "คุณจะไปไหน"},
        {"thai": "...อยู่ไหน", "romanization": "...yuu nai", "english": "Where is...?", "example": "สถานีรถไฟอยู่ไหน"},
        {"thai": "ไกลไหม", "romanization": "glai mai", "english": "Is it far?", "example": "ไกลไหมครับ"},
        {"thai": "ใกล้", "romanization": "glai", "english": "Near / Close", "example": "อยู่ใกล้ๆ"},
        {"thai": "ไกล", "romanization": "glai", "english": "Far", "example": "ไกลมาก"},
        {"thai": "ซ้าย", "romanization": "saai", "english": "Left", "example": "เลี้ยวซ้าย"},
        {"thai": "ขวา", "romanization": "khwaa", "english": "Right", "example": "เลี้ยวขวา"},
        {"thai": "ตรงไป", "romanization": "trong pai", "english": "Go straight", "example": "ตรงไปเลย"},
        {"thai": "จอดที่นี่", "romanization": "jot tii nii", "english": "Stop here", "example": "ขอจอดที่นี่"},
        {"thai": "แท็กซี่", "romanization": "taxi", "english": "Taxi", "example": "เรียกแท็กซี่หน่อย"},
    ]
    
    # Colors (Intermediate Vocabulary)
    colors_data = [
        {"thai": "สี", "romanization": "sii", "english": "Color", "example": "สีอะไร (What color?)"},
        {"thai": "สีแดง", "romanization": "sii daeng", "english": "Red", "example": "เสื้อสีแดง"},
        {"thai": "สีน้ำเงิน", "romanization": "sii naam-ngern", "english": "Blue", "example": "ท้องฟ้าสีน้ำเงิน"},
        {"thai": "สีเขียว", "romanization": "sii khiaw", "english": "Green", "example": "ต้นไม้สีเขียว"},
        {"thai": "สีเหลือง", "romanization": "sii lueang", "english": "Yellow", "example": "กล้วยสีเหลือง"},
        {"thai": "สีส้ม", "romanization": "sii som", "english": "Orange", "example": "ส้มสีส้ม"},
        {"thai": "สีม่วง", "romanization": "sii muang", "english": "Purple", "example": "ดอกไม้สีม่วง"},
        {"thai": "สีชมพู", "romanization": "sii chom-puu", "english": "Pink", "example": "สีชมพูสวย"},
        {"thai": "สีดำ", "romanization": "sii dam", "english": "Black", "example": "รองเท้าสีดำ"},
        {"thai": "สีขาว", "romanization": "sii khao", "english": "White", "example": "เสื้อสีขาว"},
        {"thai": "สีเทา", "romanization": "sii thao", "english": "Gray", "example": "ฟ้าสีเทา"},
        {"thai": "สีน้ำตาล", "romanization": "sii naam-taan", "english": "Brown", "example": "หมาสีน้ำตาล"},
    ]
    
    # Family Members
    family_data = [
        {"thai": "ครอบครัว", "romanization": "khrop-khrua", "english": "Family", "example": "ครอบครัวของฉัน"},
        {"thai": "พ่อ", "romanization": "phor", "english": "Father", "example": "พ่อของฉัน"},
        {"thai": "แม่", "romanization": "mae", "english": "Mother", "example": "แม่ของฉัน"},
        {"thai": "พี่ชาย", "romanization": "phii chaai", "english": "Older brother", "example": "พี่ชายคนโต"},
        {"thai": "พี่สาว", "romanization": "phii sao", "english": "Older sister", "example": "พี่สาวสวย"},
        {"thai": "น้องชาย", "romanization": "nong chaai", "english": "Younger brother", "example": "น้องชายตัวเล็ก"},
        {"thai": "น้องสาว", "romanization": "nong sao", "english": "Younger sister", "example": "น้องสาวน่ารัก"},
        {"thai": "ปู่", "romanization": "puu", "english": "Grandfather (paternal)", "example": "ปู่อายุมาก"},
        {"thai": "ย่า", "romanization": "yaa", "english": "Grandmother (paternal)", "example": "ย่าอายุ 80"},
        {"thai": "ตา", "romanization": "taa", "english": "Grandfather (maternal)", "example": "ตาของฉัน"},
        {"thai": "ยาย", "romanization": "yaai", "english": "Grandmother (maternal)", "example": "ยายอยู่บ้าน"},
        {"thai": "ลูก", "romanization": "luuk", "english": "Child", "example": "ลูกชาย, ลูกสาว"},
    ]
    
    # Animals (Expanded)
    animals_data = [
        {"thai": "สัตว์", "romanization": "sat", "english": "Animal", "example": "สัตว์เลี้ยง (pet)"},
        {"thai": "หมา", "romanization": "maa", "english": "Dog", "example": "หมาน่ารัก"},
        {"thai": "แมว", "romanization": "maew", "english": "Cat", "example": "แมวขาว"},
        {"thai": "นก", "romanization": "nok", "english": "Bird", "example": "นกบิน"},
        {"thai": "ปลา", "romanization": "plaa", "english": "Fish", "example": "ปลาว่าย"},
        {"thai": "ช้าง", "romanization": "chaang", "english": "Elephant", "example": "ช้างไทย"},
        {"thai": "ม้า", "romanization": "maa", "english": "Horse", "example": "ม้าวิ่ง"},
        {"thai": "วัว", "romanization": "wua", "english": "Cow", "example": "วัวกินหญ้า"},
        {"thai": "หมู", "romanization": "muu", "english": "Pig", "example": "หมูอ้วน"},
        {"thai": "ไก่", "romanization": "gai", "english": "Chicken", "example": "ไก่ขัน"},
        {"thai": "เป็ด", "romanization": "pet", "english": "Duck", "example": "เป็ดว่ายน้ำ"},
        {"thai": "ลิง", "romanization": "ling", "english": "Monkey", "example": "ลิงกินกล้วย"},
        {"thai": "เสือ", "romanization": "suea", "english": "Tiger", "example": "เสือดุร้าย"},
        {"thai": "หมี", "romanization": "mii", "english": "Bear", "example": "หมีขั้วโลก"},
        {"thai": "สิงโต", "romanization": "sing-toh", "english": "Lion", "example": "สิงโตเป็นราชสีห์"},
        {"thai": "กระต่าย", "romanization": "gra-taai", "english": "Rabbit", "example": "กระต่ายกระโดด"},
        {"thai": "เต่า", "romanization": "tao", "english": "Turtle", "example": "เต่าเดินช้า"},
        {"thai": "งู", "romanization": "nguu", "english": "Snake", "example": "งูพิษ"},
        {"thai": "จระเข้", "romanization": "jor-ra-kheh", "english": "Crocodile", "example": "จระเข้อันตราย"},
        {"thai": "กบ", "romanization": "gop", "english": "Frog", "example": "กบกระโดด"},
        {"thai": "หนู", "romanization": "nuu", "english": "Mouse/Rat", "example": "หนูเล็ก"},
        {"thai": "ควาย", "romanization": "khwaai", "english": "Buffalo", "example": "ควายไทย"},
        {"thai": "แพะ", "romanization": "phae", "english": "Goat", "example": "แพะกินหญ้า"},
        {"thai": "แกะ", "romanization": "gae", "english": "Sheep", "example": "แกะขนฟู"},
    ]
    
    # Insects
    insects_data = [
        {"thai": "แมลง", "romanization": "ma-laeng", "english": "Insect", "example": "แมลงบิน"},
        {"thai": "ผีเสื้อ", "romanization": "phii-suea", "english": "Butterfly", "example": "ผีเสื้อสวย"},
        {"thai": "ผึ้ง", "romanization": "phueng", "english": "Bee", "example": "ผึ้งทำน้ำผึ้ง"},
        {"thai": "ต่อ", "romanization": "tor", "english": "Wasp", "example": "ต่อต่อย"},
        {"thai": "มด", "romanization": "mot", "english": "Ant", "example": "มดดำ"},
        {"thai": "ยุง", "romanization": "yung", "english": "Mosquito", "example": "ยุงกัด"},
        {"thai": "แมลงวัน", "romanization": "ma-laeng wan", "english": "Fly", "example": "แมลงวันบิน"},
        {"thai": "แมลงสาบ", "romanization": "ma-laeng saap", "english": "Cockroach", "example": "แมลงสาบน่ากลัว"},
        {"thai": "ตั๊กแตน", "romanization": "tak-taen", "english": "Grasshopper", "example": "ตั๊กแตนกระโดด"},
        {"thai": "แมลงปอ", "romanization": "ma-laeng por", "english": "Dragonfly", "example": "แมลงปอสีสวย"},
        {"thai": "จิ้งหรีด", "romanization": "jing-reet", "english": "Cricket", "example": "จิ้งหรีดร้อง"},
        {"thai": "หนอนผีเสื้อ", "romanization": "norn phii-suea", "english": "Caterpillar", "example": "หนอนเป็นผีเสื้อ"},
        {"thai": "แมงมุม", "romanization": "maeng-mum", "english": "Spider", "example": "แมงมุมทอใย"},
        {"thai": "ด้วง", "romanization": "duang", "english": "Beetle", "example": "ด้วงหนามยาว"},
    ]
    
    # Plants and Trees
    plants_data = [
        {"thai": "ต้นไม้", "romanization": "ton-mai", "english": "Tree", "example": "ต้นไม้ใหญ่"},
        {"thai": "พื้ช", "romanization": "phuet", "english": "Plant", "example": "พืชสีเขียว"},
        {"thai": "ดอกไม้", "romanization": "dork-mai", "english": "Flower", "example": "ดอกไม้สวย"},
        {"thai": "หญ้า", "romanization": "yaa", "english": "Grass", "example": "หญ้าเขียว"},
        {"thai": "ใบไม้", "romanization": "bai-mai", "english": "Leaf", "example": "ใบไม้ร่วง"},
        {"thai": "ราก", "romanization": "raak", "english": "Root", "example": "รากต้นไม้"},
        {"thai": "กิ่งไม้", "romanization": "ging-mai", "english": "Branch", "example": "กิ่งไม้แตก"},
        {"thai": "เมล็ด", "romanization": "ma-let", "english": "Seed", "example": "เมล็ดพืช"},
        {"thai": "ดอกกุหลาบ", "romanization": "dork gu-laap", "english": "Rose", "example": "ดอกกุหลาบแดง"},
        {"thai": "ดอกบัว", "romanization": "dork bua", "english": "Lotus", "example": "ดอกบัวบาน"},
        {"thai": "ดอกกล้วยไม้", "romanization": "dork gluay-mai", "english": "Orchid", "example": "ดอกกล้วยไม้สวย"},
        {"thai": "ต้นมะพร้าว", "romanization": "ton ma-phrao", "english": "Coconut tree", "example": "ต้นมะพร้าวสูง"},
        {"thai": "ต้นกล้วย", "romanization": "ton gluay", "english": "Banana tree", "example": "ต้นกล้วยมีลูก"},
        {"thai": "ต้นมะม่วง", "romanization": "ton ma-muang", "english": "Mango tree", "example": "ต้นมะม่วงให้ผล"},
        {"thai": "ไผ่", "romanization": "phai", "english": "Bamboo", "example": "ต้นไผ่เติบโตเร็ว"},
    ]
    
    # Automotive Parts
    automotive_data = [
        {"thai": "รถ", "romanization": "rot", "english": "Car/Vehicle", "example": "รถยนต์"},
        {"thai": "เครื่องยนต์", "romanization": "khrueng-yon", "english": "Engine", "example": "เครื่องยนต์แรง"},
        {"thai": "ล้อ", "romanization": "lor", "english": "Wheel", "example": "ล้อรถ"},
        {"thai": "ยาง", "romanization": "yaang", "english": "Tire", "example": "ยางรถแบน"},
        {"thai": "พวงมาลัย", "romanization": "phuang-maa-lai", "english": "Steering wheel", "example": "หมุนพวงมาลัย"},
        {"thai": "เบรก", "romanization": "break", "english": "Brake", "example": "เหยียบเบรก"},
        {"thai": "คันเร่ง", "romanization": "khan reng", "english": "Accelerator", "example": "เหยียบคันเร่ง"},
        {"thai": "เกียร์", "romanization": "gear", "english": "Gear", "example": "เปลี่ยนเกียร์"},
        {"thai": "ไฟหน้า", "romanization": "fai naa", "english": "Headlight", "example": "เปิดไฟหน้า"},
        {"thai": "ไฟท้าย", "romanization": "fai thaai", "english": "Taillight", "example": "ไฟท้ายแดง"},
        {"thai": "กระจก", "romanization": "gra-jok", "english": "Mirror/Window", "example": "กระจกหลัง"},
        {"thai": "ประตู", "romanization": "pra-tuu", "english": "Door", "example": "ประตูรถ"},
        {"thai": "กระโปรงหน้า", "romanization": "gra-proong naa", "english": "Hood", "example": "เปิดกระโปรงหน้า"},
        {"thai": "ท้ายรถ", "romanization": "thaai rot", "english": "Trunk", "example": "เปิดท้ายรถ"},
        {"thai": "เข็มขัดนิรภัย", "romanization": "khem-khat ni-ra-phai", "english": "Seatbelt", "example": "คาดเข็มขัดนิรภัย"},
        {"thai": "แบตเตอรี่", "romanization": "battery", "english": "Battery", "example": "แบตเตอรี่หมด"},
    ]
    
    # Human Anatomy
    anatomy_data = [
        {"thai": "ร่างกาย", "romanization": "raang-gaai", "english": "Body", "example": "ร่างกายแข็งแรง"},
        {"thai": "หัว", "romanization": "hua", "english": "Head", "example": "ศีรษะ, หัว"},
        {"thai": "หน้า", "romanization": "naa", "english": "Face", "example": "ใบหน้า"},
        {"thai": "ตา", "romanization": "taa", "english": "Eye", "example": "ตาสองข้าง"},
        {"thai": "หู", "romanization": "huu", "english": "Ear", "example": "หูสองข้าง"},
        {"thai": "จมูก", "romanization": "ja-muuk", "english": "Nose", "example": "จมูกดม"},
        {"thai": "ปาก", "romanization": "paak", "english": "Mouth", "example": "เปิดปาก"},
        {"thai": "ฟัน", "romanization": "fan", "english": "Tooth/Teeth", "example": "ฟันขาว"},
        {"thai": "ลิ้น", "romanization": "lin", "english": "Tongue", "example": "ลิ้นชิม"},
        {"thai": "คอ", "romanization": "khor", "english": "Neck", "example": "คอยาว"},
        {"thai": "ไหล่", "romanization": "lai", "english": "Shoulder", "example": "ไหล่กว้าง"},
        {"thai": "แขน", "romanization": "khaen", "english": "Arm", "example": "แขนแข็งแรง"},
        {"thai": "มือ", "romanization": "mue", "english": "Hand", "example": "มือสอง"},
        {"thai": "นิ้ว", "romanization": "niw", "english": "Finger", "example": "นิ้วห้านิ้ว"},
        {"thai": "อก", "romanization": "ok", "english": "Chest", "example": "อกกว้าง"},
        {"thai": "หลัง", "romanization": "lang", "english": "Back", "example": "หลังตรง"},
        {"thai": "ท้อง", "romanization": "thong", "english": "Stomach/Belly", "example": "ท้องหิว"},
        {"thai": "ขา", "romanization": "khaa", "english": "Leg", "example": "ขายาว"},
        {"thai": "เท้า", "romanization": "thao", "english": "Foot", "example": "เท้าสอง"},
        {"thai": "หัวใจ", "romanization": "hua-jai", "english": "Heart", "example": "หัวใจเต้น"},
    ]
    
    # Household Items
    household_data = [
        {"thai": "บ้าน", "romanization": "baan", "english": "House/Home", "example": "บ้านหลังใหญ่"},
        {"thai": "ห้อง", "romanization": "hong", "english": "Room", "example": "ห้องนอน"},
        {"thai": "ประตู", "romanization": "pra-tuu", "english": "Door", "example": "เปิดประตู"},
        {"thai": "หน้าต่าง", "romanization": "naa-taang", "english": "Window", "example": "เปิดหน้าต่าง"},
        {"thai": "โต๊ะ", "romanization": "toh", "english": "Table", "example": "โต๊ะทำงาน"},
        {"thai": "เก้าอี้", "romanization": "gao-ee", "english": "Chair", "example": "เก้าอี้นั่ง"},
        {"thai": "เตียง", "romanization": "tiang", "english": "Bed", "example": "เตียงนอน"},
        {"thai": "หมอน", "romanization": "morn", "english": "Pillow", "example": "หมอนนุ่ม"},
        {"thai": "ผ้าห่ม", "romanization": "phaa hom", "english": "Blanket", "example": "ผ้าห่มอุ่น"},
        {"thai": "ตู้", "romanization": "tuu", "english": "Cabinet/Closet", "example": "ตู้เสื้อผ้า"},
        {"thai": "ตู้เย็น", "romanization": "tuu yen", "english": "Refrigerator", "example": "เปิดตู้เย็น"},
        {"thai": "เตาไฟ", "romanization": "tao fai", "english": "Stove", "example": "เตาไฟฟ้า"},
        {"thai": "ทีวี", "romanization": "TV", "english": "Television", "example": "ดูทีวี"},
        {"thai": "พัดลม", "romanization": "phat-lom", "english": "Fan", "example": "เปิดพัดลม"},
        {"thai": "แอร์", "romanization": "air", "english": "Air conditioner", "example": "เปิดแอร์"},
        {"thai": "โคมไฟ", "romanization": "khom-fai", "english": "Lamp", "example": "เปิดโคมไฟ"},
        {"thai": "จาน", "romanization": "jaan", "english": "Plate/Dish", "example": "จานข้าว"},
        {"thai": "ชาม", "romanization": "chaam", "english": "Bowl", "example": "ชามซุป"},
        {"thai": "ช้อน", "romanization": "chon", "english": "Spoon", "example": "ช้อนกิน"},
        {"thai": "ส้อม", "romanization": "som", "english": "Fork", "example": "ส้อมและมีด"},
        {"thai": "มีด", "romanization": "meet", "english": "Knife", "example": "มีดหั่น"},
        {"thai": "แก้ว", "romanization": "gaew", "english": "Glass/Cup", "example": "แก้วน้ำ"},
    ]
    
    # Clothing
    clothing_data = [
        {"thai": "เสื้อผ้า", "romanization": "suea-phaa", "english": "Clothes", "example": "เสื้อผ้าสะอาด"},
        {"thai": "เสื้อ", "romanization": "suea", "english": "Shirt/Top", "example": "เสื้อสวย"},
        {"thai": "กางเกง", "romanization": "gaang-geng", "english": "Pants/Trousers", "example": "กางเกงยีน"},
        {"thai": "กระโปรง", "romanization": "gra-proong", "english": "Skirt", "example": "กระโปรงสั้น"},
        {"thai": "ชุด", "romanization": "chut", "english": "Dress/Outfit", "example": "ชุดสวย"},
        {"thai": "เสื้อโค้ท", "romanization": "suea-coat", "english": "Coat", "example": "เสื้อโค้ทหนา"},
        {"thai": "เสื้อแจ็คเก็ต", "romanization": "suea jacket", "english": "Jacket", "example": "แจ็คเก็ตหนัง"},
        {"thai": "รองเท้า", "romanization": "rong-thao", "english": "Shoes", "example": "รองเท้าคู่ใหม่"},
        {"thai": "ถุงเท้า", "romanization": "thung-thao", "english": "Socks", "example": "ถุงเท้าคู่หนึ่ง"},
        {"thai": "หมวก", "romanization": "muak", "english": "Hat/Cap", "example": "หมวกกันแดด"},
        {"thai": "เข็มขัด", "romanization": "khem-khat", "english": "Belt", "example": "เข็มขัดหนัง"},
        {"thai": "กระเป๋า", "romanization": "gra-pao", "english": "Bag", "example": "กระเป๋าถือ"},
        {"thai": "ผ้าพันคอ", "romanization": "phaa-phan-khor", "english": "Scarf", "example": "ผ้าพันคออุ่น"},
        {"thai": "แว่นตา", "romanization": "waen-taa", "english": "Glasses", "example": "แว่นตาสายตา"},
        {"thai": "ชุดชั้นใน", "romanization": "chut-chan-nai", "english": "Underwear", "example": "ชุดชั้นในสะอาด"},
    ]
    
    # Emotions and Feelings
    emotions_data = [
        {"thai": "ความรู้สึก", "romanization": "khwaam-ruu-suek", "english": "Feeling/Emotion", "example": "ความรู้สึกดี"},
        {"thai": "มีความสุข", "romanization": "mii khwaam-suk", "english": "Happy", "example": "ฉันมีความสุข"},
        {"thai": "เศร้า", "romanization": "sao", "english": "Sad", "example": "รู้สึกเศร้า"},
        {"thai": "โกรธ", "romanization": "groht", "english": "Angry", "example": "โกรธมาก"},
        {"thai": "กลัว", "romanization": "glua", "english": "Scared/Afraid", "example": "กลัวผี"},
        {"thai": "ตื่นเต้น", "romanization": "teun-ten", "english": "Excited", "example": "ตื่นเต้นมาก"},
        {"thai": "เบื่อ", "romanization": "buea", "english": "Bored", "example": "เบื่อมาก"},
        {"thai": "รัก", "romanization": "rak", "english": "Love", "example": "รักเธอ"},
        {"thai": "เกลียด", "romanization": "gliiat", "english": "Hate", "example": "เกลียดแมลงสาบ"},
        {"thai": "ประหลาดใจ", "romanization": "pra-laat-jai", "english": "Surprised", "example": "ประหลาดใจมาก"},
        {"thai": "เหนื่อย", "romanization": "nuay", "english": "Tired", "example": "เหนื่อยมาก"},
        {"thai": "เครียด", "romanization": "kriiat", "english": "Stressed", "example": "รู้สึกเครียด"},
        {"thai": "ผ่อนคลาย", "romanization": "phon-khlaai", "english": "Relaxed", "example": "รู้สึกผ่อนคลาย"},
        {"thai": "เหงา", "romanization": "ngao", "english": "Lonely", "example": "รู้สึกเหงา"},
        {"thai": "ภูมิใจ", "romanization": "phuum-jai", "english": "Proud", "example": "ภูมิใจในตัวเอง"},
        {"thai": "อิจฉา", "romanization": "it-chaa", "english": "Jealous", "example": "อิจฉาเธอ"},
        {"thai": "กังวล", "romanization": "gang-won", "english": "Worried/Anxious", "example": "กังวลเรื่องนี้"},
        {"thai": "สับสน", "romanization": "sap-son", "english": "Confused", "example": "รู้สึกสับสน"},
    ]
    
    # Male/Female Polite Particles
    polite_particles_data = [
        {"thai": "ครับ", "romanization": "khrap", "english": "Polite particle (male)", "example": "สวัสดีครับ (Hello - male)"},
        {"thai": "ค่ะ", "romanization": "kha", "english": "Polite particle (female)", "example": "สวัสดีค่ะ (Hello - female)"},
        {"thai": "ครับผม", "romanization": "khrap phom", "english": "Very polite (male)", "example": "ขอบคุณครับผม"},
        {"thai": "คะ", "romanization": "kha", "english": "Question ending (female)", "example": "อะไรคะ (What? - female)"},
        {"thai": "นะครับ", "romanization": "na khrap", "english": "Softening particle (male)", "example": "ไปนะครับ"},
        {"thai": "นะคะ", "romanization": "na kha", "english": "Softening particle (female)", "example": "ไปนะคะ"},
        {"thai": "ครับ/ค่ะ", "romanization": "khrap/kha", "english": "Yes (polite)", "example": "ได้ครับ/ค่ะ (Yes)"},
        {"thai": "ผม", "romanization": "phom", "english": "I (male, formal)", "example": "ผมชื่อจอห์น"},
        {"thai": "ดิฉัน", "romanization": "di-chan", "english": "I (female, formal)", "example": "ดิฉันชื่อแมรี่"},
        {"thai": "ฉัน", "romanization": "chan", "english": "I (neutral/informal)", "example": "ฉันชอบกินส้ม"},
    ]
    
    # Days of the Week
    days_data = [
        {"thai": "วัน", "romanization": "wan", "english": "Day", "example": "วันนี้ (today)"},
        {"thai": "วันจันทร์", "romanization": "wan jan", "english": "Monday", "example": "วันจันทร์ทำงาน"},
        {"thai": "วันอังคาร", "romanization": "wan ang-khaan", "english": "Tuesday", "example": "วันอังคารหน้า"},
        {"thai": "วันพุธ", "romanization": "wan phut", "english": "Wednesday", "example": "วันพุธนี้"},
        {"thai": "วันพฤหัสบดี", "romanization": "wan pha-rueh-hat", "english": "Thursday", "example": "ทุกวันพฤหัสบดี"},
        {"thai": "วันศุกร์", "romanization": "wan suk", "english": "Friday", "example": "วันศุกร์สนุก"},
        {"thai": "วันเสาร์", "romanization": "wan sao", "english": "Saturday", "example": "วันเสาร์พักผ่อน"},
        {"thai": "วันอาทิตย์", "romanization": "wan aa-thit", "english": "Sunday", "example": "วันอาทิตย์ไปวัด"},
        {"thai": "วันนี้", "romanization": "wan nii", "english": "Today", "example": "วันนี้อากาศดี"},
        {"thai": "เมื่อวาน", "romanization": "muea waan", "english": "Yesterday", "example": "เมื่อวานฉันไป"},
        {"thai": "พรุ่งนี้", "romanization": "phrung-nii", "english": "Tomorrow", "example": "พรุ่งนี้เจอกัน"},
    ]
    
    # Time Expressions
    time_data = [
        {"thai": "เวลา", "romanization": "wee-laa", "english": "Time", "example": "เวลาเท่าไหร่"},
        {"thai": "ตอนเช้า", "romanization": "torn chao", "english": "Morning", "example": "ตอนเช้าสดชื่น"},
        {"thai": "ตอนกลางวัน", "romanization": "torn glaang wan", "english": "Noon/Afternoon", "example": "ตอนกลางวันร้อน"},
        {"thai": "ตอนเย็น", "romanization": "torn yen", "english": "Evening", "example": "ตอนเย็นเย็นสบาย"},
        {"thai": "ตอนกลางคืน", "romanization": "torn glaang kheun", "english": "Night", "example": "ตอนกลางคืนหลับ"},
        {"thai": "นาที", "romanization": "naa-thii", "english": "Minute", "example": "สิบนาที (10 minutes)"},
        {"thai": "ชั่วโมง", "romanization": "chua-moong", "english": "Hour", "example": "สองชั่วโมง"},
        {"thai": "วินาที", "romanization": "wi-naa-thii", "english": "Second", "example": "ห้าวินาที"},
        {"thai": "เดี๋ยวนี้", "romanization": "diaw-nii", "english": "Now/Right now", "example": "ไปเดี๋ยวนี้"},
        {"thai": "เร็วๆ นี้", "romanization": "rew rew nii", "english": "Soon", "example": "เจอกันเร็วๆ นี้"},
        {"thai": "ทีหลัง", "romanization": "thii-lang", "english": "Later", "example": "คุยกันทีหลัง"},
    ]
    
    # Question Words (Essential for intermediate)
    questions_data = [
        {"thai": "อะไร", "romanization": "arai", "english": "What", "example": "นี่คืออะไร (What is this?)"},
        {"thai": "ที่ไหน", "romanization": "thii-nai", "english": "Where", "example": "คุณอยู่ที่ไหน"},
        {"thai": "เมื่อไหร่", "romanization": "muea-rai", "english": "When", "example": "ไปเมื่อไหร่"},
        {"thai": "ทำไม", "romanization": "tham-mai", "english": "Why", "example": "ทำไมถึงไป"},
        {"thai": "อย่างไร", "romanization": "yaang-rai", "english": "How", "example": "ทำอย่างไร"},
        {"thai": "ใคร", "romanization": "khrai", "english": "Who", "example": "คนนี้ใคร"},
        {"thai": "เท่าไหร่", "romanization": "thao-rai", "english": "How much/many", "example": "ราคาเท่าไหร่"},
        {"thai": "กี่", "romanization": "gii", "english": "How many", "example": "กี่คน (How many people?)"},
        {"thai": "ไหน", "romanization": "nai", "english": "Which", "example": "อันไหน (Which one?)"},
    ]
    
    # Shopping & Money
    shopping_data = [
        {"thai": "ซื้อ", "romanization": "sue", "english": "Buy", "example": "ซื้อของ"},
        {"thai": "ขาย", "romanization": "khaai", "english": "Sell", "example": "ขายอะไร"},
        {"thai": "เงิน", "romanization": "ngern", "english": "Money", "example": "มีเงินไหม"},
        {"thai": "บาท", "romanization": "baat", "english": "Baht (currency)", "example": "สิบบาท"},
        {"thai": "แพง", "romanization": "phaeng", "english": "Expensive", "example": "แพงมาก"},
        {"thai": "ถูก", "romanization": "thuuk", "english": "Cheap", "example": "ถูกดี"},
        {"thai": "ลด", "romanization": "lot", "english": "Discount", "example": "ลดราคา"},
        {"thai": "ตลาด", "romanization": "ta-laat", "english": "Market", "example": "ไปตลาด"},
        {"thai": "ร้าน", "romanization": "raan", "english": "Shop/Store", "example": "ร้านอาหาร"},
        {"thai": "จ่าย", "romanization": "jaai", "english": "Pay", "example": "จ่ายเงิน"},
        {"thai": "ทอน", "romanization": "thon", "english": "Change (money)", "example": "เงินทอน"},
    ]
    
    # Emergency & Health
    emergency_data = [
        {"thai": "ฉุกเฉิน", "romanization": "chuk-chern", "english": "Emergency", "example": "สถานการณ์ฉุกเฉิน"},
        {"thai": "ช่วยด้วย", "romanization": "chuay duay", "english": "Help!", "example": "ช่วยด้วยครับ"},
        {"thai": "โรงพยาบาล", "romanization": "roong-pha-yaa-baan", "english": "Hospital", "example": "ไปโรงพยาบาล"},
        {"thai": "หมอ", "romanization": "mor", "english": "Doctor", "example": "เรียกหมอ"},
        {"thai": "ปวด", "romanization": "puat", "english": "Pain/Hurt", "example": "ปวดหัว (headache)"},
        {"thai": "เจ็บ", "romanization": "jep", "english": "Sick/Injured", "example": "เจ็บป่วย"},
        {"thai": "ยา", "romanization": "yaa", "english": "Medicine", "example": "กินยา"},
        {"thai": "ตำรวจ", "romanization": "tam-ruat", "english": "Police", "example": "เรียกตำรวจ"},
        {"thai": "อันตราย", "romanization": "an-ta-raai", "english": "Dangerous", "example": "อันตรายมาก"},
        {"thai": "ไฟไหม้", "romanization": "fai mai", "english": "Fire", "example": "เกิดไฟไหม้"},
    ]
    
    # Common Adjectives
    adjectives_data = [
        {"thai": "ดี", "romanization": "dii", "english": "Good", "example": "อากาศดี"},
        {"thai": "ไม่ดี", "romanization": "mai dii", "english": "Bad/Not good", "example": "อารมณ์ไม่ดี"},
        {"thai": "ใหญ่", "romanization": "yai", "english": "Big/Large", "example": "บ้านใหญ่"},
        {"thai": "เล็ก", "romanization": "lek", "english": "Small", "example": "รถเล็ก"},
        {"thai": "สูง", "romanization": "suung", "english": "Tall/High", "example": "ตึกสูง"},
        {"thai": "เตี้ย", "romanization": "tiia", "english": "Short (height)", "example": "คนเตี้ย"},
        {"thai": "ยาว", "romanization": "yaao", "english": "Long", "example": "ผมยาว"},
        {"thai": "สั้น", "romanization": "san", "english": "Short (length)", "example": "กระโปรงสั้น"},
        {"thai": "สวย", "romanization": "suay", "english": "Beautiful/Pretty", "example": "ผู้หญิงสวย"},
        {"thai": "หล่อ", "romanization": "lor", "english": "Handsome", "example": "ผู้ชายหล่อ"},
        {"thai": "น่ารัก", "romanization": "naa-rak", "english": "Cute", "example": "เด็กน่ารัก"},
        {"thai": "ร้อน", "romanization": "ron", "english": "Hot", "example": "อากาศร้อน"},
        {"thai": "หนาว", "romanization": "nao", "english": "Cold", "example": "อากาศหนาว"},
        {"thai": "เร็ว", "romanization": "rew", "english": "Fast", "example": "วิ่งเร็ว"},
        {"thai": "ช้า", "romanization": "chaa", "english": "Slow", "example": "เดินช้า"},
    ]
    
    # Basic Verbs
    verbs_data = [
        {"thai": "ไป", "romanization": "pai", "english": "Go", "example": "ไปทำงาน"},
        {"thai": "มา", "romanization": "maa", "english": "Come", "example": "มาที่นี่"},
        {"thai": "กิน", "romanization": "gin", "english": "Eat", "example": "กินข้าว"},
        {"thai": "ดื่ม", "romanization": "duem", "english": "Drink", "example": "ดื่มน้ำ"},
        {"thai": "นอน", "romanization": "norn", "english": "Sleep", "example": "นอนหลับ"},
        {"thai": "ตื่น", "romanization": "teun", "english": "Wake up", "example": "ตื่นนอน"},
        {"thai": "ทำ", "romanization": "tham", "english": "Do/Make", "example": "ทำงาน"},
        {"thai": "อ่าน", "romanization": "aan", "english": "Read", "example": "อ่านหนังสือ"},
        {"thai": "เขียน", "romanization": "khian", "english": "Write", "example": "เขียนจดหมาย"},
        {"thai": "พูด", "romanization": "phuut", "english": "Speak", "example": "พูดภาษาไทย"},
        {"thai": "ฟัง", "romanization": "fang", "english": "Listen", "example": "ฟังเพลง"},
        {"thai": "ดู", "romanization": "duu", "english": "Look/Watch", "example": "ดูทีวี"},
        {"thai": "รัก", "romanization": "rak", "english": "Love", "example": "รักเธอ"},
        {"thai": "ชอบ", "romanization": "chorp", "english": "Like", "example": "ชอบกินส้ม"},
    ]
    
    # LEARNING SONGS (Copyright-Free Educational Content)
    
    # Alphabet Song
    alphabet_song_data = [
        {"thai": "ก ไก่ ข ไข่", "romanization": "gor gai, khor khai", "english": "K for Chicken, Kh for Egg", "example": "Verse 1 - Learn first 4 consonants"},
        {"thai": "ค ควาย ง งู", "romanization": "khor khwaai, ngor nguu", "english": "Kh for Buffalo, Ng for Snake", "example": "Verse 2"},
        {"thai": "จ จาน ฉ ฉิ่ง", "romanization": "jor jaan, chor ching", "english": "J for Plate, Ch for Cymbal", "example": "Verse 3"},
        {"thai": "ช ช้าง ซ โซ่", "romanization": "chor chaang, sor soh", "english": "Ch for Elephant, S for Chain", "example": "Verse 4"},
        {"thai": "ฮิป ฮิป ฮูเร สนุกจัง", "romanization": "hip hip hooray, sanuk jang", "english": "Hip hip hooray, so much fun!", "example": "Chorus - Celebration"},
        {"thai": "เรียนรู้ภาษาไทย", "romanization": "riian-ruu phaa-saa thai", "english": "Learning Thai language", "example": "Chorus continues"},
        {"thai": "ท ทหาร น หนู", "romanization": "thor tha-haan, nor nuu", "english": "Th for Soldier, N for Mouse", "example": "Verse 5"},
        {"thai": "ป ปลา ผ ผึ้ง", "romanization": "por plaa, phor phueng", "english": "P for Fish, Ph for Bee", "example": "Verse 6"},
        {"thai": "ม ม้า ย ยักษ์", "romanization": "mor maa, yor yak", "english": "M for Horse, Y for Giant", "example": "Verse 7"},
        {"thai": "ร เรือ ล ลิง", "romanization": "ror ruea, lor ling", "english": "R for Boat, L for Monkey", "example": "Verse 8"},
        {"thai": "ส เสือ ห หีบ", "romanization": "sor suea, hor hiip", "english": "S for Tiger, H for Chest", "example": "Final verse"},
        {"thai": "เก่งมากเลย!", "romanization": "geng maak loey!", "english": "Very smart!", "example": "Ending - Encouragement"},
    ]
    
    # Number Counting Songs
    number_songs_data = [
        {"thai": "หนึ่ง สอง สาม", "romanization": "neung song saam", "english": "One, Two, Three", "example": "Count 1-3 (Easy)"},
        {"thai": "สี่ ห้า หก", "romanization": "sii haa hok", "english": "Four, Five, Six", "example": "Count 4-6 (Easy)"},
        {"thai": "เจ็ด แปด เก้า", "romanization": "jet bpaet gao", "english": "Seven, Eight, Nine", "example": "Count 7-9 (Easy)"},
        {"thai": "สิบ! เยี่ยมมาก!", "romanization": "sip! yiiam maak!", "english": "Ten! Excellent!", "example": "Reach 10 - Celebration"},
        {"thai": "นับไปเรื่อยๆ ไม่มีสิ้นสุด", "romanization": "nap pai rueay-rueay mai-mii sin-sut", "english": "Keep counting, never ending", "example": "Chorus"},
        {"thai": "สิบเอ็ด สิบสอง", "romanization": "sip-et sip-song", "english": "Eleven, Twelve", "example": "Continue to 11-12"},
        {"thai": "สิบสาม สิบสี่ สิบห้า", "romanization": "sip-saam sip-sii sip-haa", "english": "Thirteen, Fourteen, Fifteen", "example": "Count 13-15"},
        {"thai": "ยี่สิบ! ครึ่งทางแล้ว", "romanization": "yii-sip! khrueng-thaang laew", "english": "Twenty! Halfway there", "example": "Milestone at 20"},
        {"thai": "ห้าสิบ หกสิบ เจ็ดสิบ", "romanization": "haa-sip hok-sip jet-sip", "english": "Fifty, Sixty, Seventy", "example": "Big numbers"},
        {"thai": "แปดสิบ เก้าสิบ หนึ่งร้อย!", "romanization": "bpaet-sip gao-sip neung-roi!", "english": "Eighty, Ninety, One Hundred!", "example": "Reach 100 - Victory!"},
    ]
    
    # Daily Routine Song
    daily_routine_song_data = [
        {"thai": "ตอนเช้าตื่นนอน", "romanization": "torn-chao teun-norn", "english": "In the morning, wake up", "example": "Morning routine starts"},
        {"thai": "แปรงฟันล้างหน้า", "romanization": "bpraeng-fan laang-naa", "english": "Brush teeth, wash face", "example": "Hygiene routine"},
        {"thai": "กินข้าวเช้าอร่อย", "romanization": "gin-khao-chao aroi", "english": "Eat delicious breakfast", "example": "Breakfast time"},
        {"thai": "ไปโรงเรียน", "romanization": "pai roong-riian", "english": "Go to school", "example": "Morning activity"},
        {"thai": "เรียนหนังสือตั้งใจ", "romanization": "riian nang-sue tang-jai", "english": "Study books diligently", "example": "School time"},
        {"thai": "กลับบ้านตอนเย็น", "romanization": "glap-baan torn-yen", "english": "Return home in the evening", "example": "After school"},
        {"thai": "ทำการบ้านเสร็จ", "romanization": "tham gaan-baan set", "english": "Finish homework", "example": "Evening routine"},
        {"thai": "เล่นกับเพื่อน", "romanization": "len gap phuean", "english": "Play with friends", "example": "Recreation time"},
        {"thai": "กินข้าวเย็นกับครอบครัว", "romanization": "gin khao-yen gap khrop-khrua", "english": "Eat dinner with family", "example": "Family time"},
        {"thai": "อาบน้ำก่อนนอน", "romanization": "aap-naam gorn-norn", "english": "Take a bath before bed", "example": "Bedtime prep"},
        {"thai": "นอนหลับฝันดี", "romanization": "norn-lap fan-dii", "english": "Sleep well, sweet dreams", "example": "Goodnight"},
    ]
    
    # Colors Song
    colors_song_data = [
        {"thai": "สีแดง สีแดง เหมือนแอปเปิ้ล", "romanization": "sii-daeng sii-daeng muean apple", "english": "Red, red, like an apple", "example": "Red color verse"},
        {"thai": "สีน้ำเงิน ท้องฟ้าสวย", "romanization": "sii-naam-ngern thong-faa suay", "english": "Blue, beautiful sky", "example": "Blue color verse"},
        {"thai": "สีเขียว สีเขียว ต้นไม้เขียว", "romanization": "sii-khiaw sii-khiaw ton-mai khiaw", "english": "Green, green, green trees", "example": "Green color verse"},
        {"thai": "สีเหลือง สดใส", "romanization": "sii-lueang sot-sai", "english": "Yellow, bright and cheerful", "example": "Yellow color verse"},
        {"thai": "รุ้งกินน้ำ เจ็ดสี", "romanization": "rung-gin-naam jet-sii", "english": "Rainbow has seven colors", "example": "Chorus about rainbow"},
        {"thai": "สวยงามมาก", "romanization": "suay-ngaam maak", "english": "Very beautiful", "example": "Appreciation"},
        {"thai": "สีส้ม สีส้ม หวานๆ", "romanization": "sii-som sii-som waan-waan", "english": "Orange, orange, sweet", "example": "Orange color"},
        {"thai": "สีม่วง สวยหรู", "romanization": "sii-muang suay-ruu", "english": "Purple, elegant", "example": "Purple color"},
        {"thai": "สีชมพู น่ารัก", "romanization": "sii-chom-puu naa-rak", "english": "Pink, cute", "example": "Pink color"},
        {"thai": "สีขาว สีดำ", "romanization": "sii-khao sii-dam", "english": "White and black", "example": "Final colors"},
    ]
    
    # Animal Sounds Song
    animals_song_data = [
        {"thai": "หมาเห่า โฮ่ง โฮ่ง", "romanization": "maa hao hong hong", "english": "Dog barks: woof woof", "example": "Dog sound"},
        {"thai": "แมวร้อง เหมียว เหมียว", "romanization": "maew rong miaw miaw", "english": "Cat meows: meow meow", "example": "Cat sound"},
        {"thai": "วัวร้อง มอ มอ", "romanization": "wua rong mor mor", "english": "Cow moos: moo moo", "example": "Cow sound"},
        {"thai": "เป็ดร้อง แว๊บ แว๊บ", "romanization": "pet rong waep waep", "english": "Duck quacks: quack quack", "example": "Duck sound"},
        {"thai": "สัตว์ต่างๆ เสียงสนุก", "romanization": "sat-taang-taang siang-sanuk", "english": "Different animals, fun sounds", "example": "Chorus"},
        {"thai": "ไก่ขัน กุ๊ก กุ๊ก อีแก", "romanization": "gai khan gook gook ii-gae", "english": "Rooster crows: cock-a-doodle-doo", "example": "Rooster sound"},
        {"thai": "หมูร้อง อู้ด อู้ด", "romanization": "muu rong oot oot", "english": "Pig oinks: oink oink", "example": "Pig sound"},
        {"thai": "นกร้อง จิ๊บ จิ๊บ", "romanization": "nok rong jip jip", "english": "Bird chirps: chirp chirp", "example": "Bird sound"},
        {"thai": "ช้างร้อง ปาว ปาว", "romanization": "chaang rong paao paao", "english": "Elephant trumpets", "example": "Elephant sound"},
        {"thai": "เรียนรู้เสียงสัตว์กันเถอะ", "romanization": "riian-ruu siang-sat gan ther", "english": "Let's learn animal sounds", "example": "Ending encouragement"},
    ]
    
    # Family Song
    family_song_data = [
        {"thai": "พ่อของฉันดีมาก", "romanization": "phor khong chan dii-maak", "english": "My father is very good", "example": "About father"},
        {"thai": "แม่ของฉันใจดี", "romanization": "mae khong chan jai-dii", "english": "My mother is kind-hearted", "example": "About mother"},
        {"thai": "ครอบครัวของฉัน", "romanization": "khrop-khrua khong chan", "english": "My family", "example": "Chorus about family"},
        {"thai": "รักกันมาก", "romanization": "rak-gan-maak", "english": "Love each other very much", "example": "Family love"},
        {"thai": "พี่ชายของฉันสูง", "romanization": "phii-chaai khong chan suung", "english": "My older brother is tall", "example": "About brother"},
        {"thai": "พี่สาวของฉันสวย", "romanization": "phii-sao khong chan suay", "english": "My older sister is beautiful", "example": "About sister"},
        {"thai": "น้องน้อยน่ารัก", "romanization": "nong-noi naa-rak", "english": "Little sibling is cute", "example": "About younger sibling"},
        {"thai": "ปู่ย่าตายาย", "romanization": "puu yaa taa yaai", "english": "Grandparents", "example": "About grandparents"},
        {"thai": "ทุกคนรักกัน", "romanization": "thuk-khon rak-gan", "english": "Everyone loves each other", "example": "Final message"},
    ]
    
    # Days Song
    days_song_data = [
        {"thai": "วันจันทร์ วันจันทร์", "romanization": "wan-jan wan-jan", "english": "Monday, Monday", "example": "Monday verse"},
        {"thai": "วันอังคาร ทำงาน", "romanization": "wan-ang-khaan tham-ngaan", "english": "Tuesday, work day", "example": "Tuesday verse"},
        {"thai": "วันพุธ กลางสัปดาห์", "romanization": "wan-phut glaang-sap-daa", "english": "Wednesday, middle of week", "example": "Wednesday verse"},
        {"thai": "วันพฤหัสบดี มีความสุข", "romanization": "wan-pha-rueh-hat mii-khwaam-suk", "english": "Thursday, happy day", "example": "Thursday verse"},
        {"thai": "เจ็ดวัน เจ็ดวัน", "romanization": "jet-wan jet-wan", "english": "Seven days, seven days", "example": "Chorus - week has 7 days"},
        {"thai": "วันศุกร์ เย้! ใกล้หยุด", "romanization": "wan-suk yay! glai-yut", "english": "Friday, yay! Almost weekend", "example": "Friday excitement"},
        {"thai": "วันเสาร์ เล่นสนุก", "romanization": "wan-sao len-sanuk", "english": "Saturday, play and have fun", "example": "Saturday fun"},
        {"thai": "วันอาทิตย์ พักผ่อน", "romanization": "wan-aa-thit phak-phon", "english": "Sunday, rest and relax", "example": "Sunday rest"},
        {"thai": "สัปดาห์ใหม่เริ่มอีกครั้ง", "romanization": "sap-daa-mai ruem iik-khrang", "english": "New week starts again", "example": "Week cycle"},
    ]
    
    # Body Parts Song  
    body_song_data = [
        {"thai": "หัวเข่าไหล่ เท้า", "romanization": "hua khao lai thao", "english": "Head, knees, shoulders, feet", "example": "Body parts rhythm"},
        {"thai": "เท้า เท้า", "romanization": "thao thao", "english": "Feet, feet", "example": "Repeat feet"},
        {"thai": "ตา หู ปาก จมูก", "romanization": "taa huu paak ja-muuk", "english": "Eyes, ears, mouth, nose", "example": "Face parts"},
        {"thai": "แขน มือ นิ้ว", "romanization": "khaen mue niw", "english": "Arms, hands, fingers", "example": "Upper body"},
        {"thai": "ขยับ ขยับ", "romanization": "kha-yap kha-yap", "english": "Move, move", "example": "Action - moving"},
        {"thai": "โบกมือ โบกมือ", "romanization": "boke-mue boke-mue", "english": "Wave hand, wave hand", "example": "Hand action"},
        {"thai": "กระโดด กระโดด", "romanization": "gra-doht gra-doht", "english": "Jump, jump", "example": "Jumping action"},
        {"thai": "ร่างกายแข็งแรง", "romanization": "raang-gaai khaeng-raeng", "english": "Strong body", "example": "Health message"},
    ]
    
    lessons = [
        {
            "title": "Thai Consonants",
            "category": "alphabet",
            "subcategory": "consonants",
            "description": "Learn all 44 Thai consonants with romanization and meanings",
            "items": consonants_data,
            "order": 1
        },
        {
            "title": "Thai Vowels",
            "category": "alphabet",
            "subcategory": "vowels",
            "description": "Master Thai vowels and their pronunciations",
            "items": vowels_data,
            "order": 2
        },
        {
            "title": "Numbers 0-100",
            "category": "numbers",
            "subcategory": "basic",
            "description": "Learn Thai numbers from 0 to 100",
            "items": numbers_basic,
            "order": 3
        },
        {
            "title": "Large Numbers",
            "category": "numbers",
            "subcategory": "large",
            "description": "Learn large Thai numbers: hundreds, thousands, up to 1 million",
            "items": numbers_large,
            "order": 4
        },
        {
            "title": "Greetings",
            "category": "conversations",
            "subcategory": "greetings",
            "description": "Essential Thai greetings and introductions",
            "items": greetings_data,
            "order": 4
        },
        {
            "title": "Common Phrases",
            "category": "conversations",
            "subcategory": "common",
            "description": "Everyday Thai phrases you need to know",
            "items": common_phrases_data,
            "order": 5
        },
        {
            "title": "Dining",
            "category": "conversations",
            "subcategory": "dining",
            "description": "Food and restaurant related phrases",
            "items": dining_data,
            "order": 6
        },
        {
            "title": "Travel",
            "category": "conversations",
            "subcategory": "travel",
            "description": "Essential phrases for getting around Thailand",
            "items": travel_data,
            "order": 5
        },
        {
            "title": "Colors",
            "category": "vocabulary",
            "subcategory": "colors",
            "description": "Learn Thai colors with examples",
            "items": colors_data,
            "order": 6
        },
        {
            "title": "Family Members",
            "category": "vocabulary",
            "subcategory": "family",
            "description": "Thai words for family relationships",
            "items": family_data,
            "order": 7
        },
        {
            "title": "Animals",
            "category": "vocabulary",
            "subcategory": "animals",
            "description": "Common animals in Thai language",
            "items": animals_data,
            "order": 8
        },
        {
            "title": "Days of the Week",
            "category": "time",
            "subcategory": "days",
            "description": "Learn Thai days and time expressions",
            "items": days_data,
            "order": 9
        },
        {
            "title": "Time Expressions",
            "category": "time",
            "subcategory": "expressions",
            "description": "Essential time-related vocabulary",
            "items": time_data,
            "order": 10
        },
        {
            "title": "Question Words",
            "category": "grammar",
            "subcategory": "questions",
            "description": "Essential question words for conversations",
            "items": questions_data,
            "order": 11
        },
        {
            "title": "Shopping & Money",
            "category": "intermediate",
            "subcategory": "shopping",
            "description": "Vocabulary for shopping and handling money",
            "items": shopping_data,
            "order": 12
        },
        {
            "title": "Emergency & Health",
            "category": "intermediate",
            "subcategory": "emergency",
            "description": "Essential phrases for emergencies and health",
            "items": emergency_data,
            "order": 13
        },
        {
            "title": "Common Adjectives",
            "category": "vocabulary",
            "subcategory": "adjectives",
            "description": "Descriptive words you'll use every day",
            "items": adjectives_data,
            "order": 14
        },
        {
            "title": "Basic Verbs",
            "category": "vocabulary",
            "subcategory": "verbs",
            "description": "Essential action words for daily use",
            "items": verbs_data,
            "order": 15
        },
        {
            "title": "Insects",
            "category": "vocabulary",
            "subcategory": "insects",
            "description": "Bugs and insects in Thai",
            "items": insects_data,
            "order": 16
        },
        {
            "title": "Plants & Trees",
            "category": "vocabulary",
            "subcategory": "plants",
            "description": "Flora, flowers, and vegetation",
            "items": plants_data,
            "order": 17
        },
        {
            "title": "Automotive Parts",
            "category": "vocabulary",
            "subcategory": "automotive",
            "description": "Car and vehicle terminology",
            "items": automotive_data,
            "order": 18
        },
        {
            "title": "Human Anatomy",
            "category": "vocabulary",
            "subcategory": "anatomy",
            "description": "Body parts and organs",
            "items": anatomy_data,
            "order": 19
        },
        {
            "title": "Household Items",
            "category": "vocabulary",
            "subcategory": "household",
            "description": "Common items found at home",
            "items": household_data,
            "order": 20
        },
        {
            "title": "Clothing",
            "category": "vocabulary",
            "subcategory": "clothing",
            "description": "Clothes and accessories",
            "items": clothing_data,
            "order": 21
        },
        {
            "title": "Emotions & Feelings",
            "category": "vocabulary",
            "subcategory": "emotions",
            "description": "Express how you feel in Thai",
            "items": emotions_data,
            "order": 22
        },
        {
            "title": "Polite Speech (Male/Female)",
            "category": "grammar",
            "subcategory": "politeness",
            "description": "Gender-specific polite particles and pronouns",
            "items": polite_particles_data,
            "order": 23
        },
        {
            "title": "Alphabet Song",
            "category": "songs",
            "subcategory": "alphabet",
            "description": "Learn Thai consonants through song",
            "items": alphabet_song_data,
            "order": 24
        },
        {
            "title": "Number Counting Songs",
            "category": "songs",
            "subcategory": "numbers",
            "description": "Fun counting songs from 1 to 100",
            "items": number_songs_data,
            "order": 25
        },
        {
            "title": "Daily Routine Song",
            "category": "songs",
            "subcategory": "daily",
            "description": "Learn daily activities through song",
            "items": daily_routine_song_data,
            "order": 26
        },
        {
            "title": "Colors & Shapes Song",
            "category": "songs",
            "subcategory": "vocabulary",
            "description": "Sing along to learn colors and shapes",
            "items": colors_song_data,
            "order": 27
        },
        {
            "title": "Animal Sounds Song",
            "category": "songs",
            "subcategory": "animals",
            "description": "Learn animals and their sounds",
            "items": animals_song_data,
            "order": 28
        },
        {
            "title": "Family Song",
            "category": "songs",
            "subcategory": "family",
            "description": "Learn family members through melody",
            "items": family_song_data,
            "order": 29
        },
        {
            "title": "Days of the Week Song",
            "category": "songs",
            "subcategory": "time",
            "description": "Memorize Thai days through song",
            "items": days_song_data,
            "order": 30
        },
        {
            "title": "Body Parts Song",
            "category": "songs",
            "subcategory": "anatomy",
            "description": "Learn body parts with catchy tune",
            "items": body_song_data,
            "order": 31
        }
    ]
    
    # Add language_mode to all Thai lessons
    for lesson in lessons:
        lesson["language_mode"] = "learn-thai"
    
    # ========== ENGLISH LEARNING CONTENT (Thai speakers learning English) ==========
    
    # English Alphabet (A-Z)
    english_alphabet_data = [
        {"thai": "เอ (สำหรับ แอปเปิล)", "romanization": "A (for Apple)", "english": "A", "example": "Apple - แอปเปิล"},
        {"thai": "บี (สำหรับ บอล)", "romanization": "B (for Ball)", "english": "B", "example": "Ball - ลูกบอล"},
        {"thai": "ซี (สำหรับ แมว)", "romanization": "C (for Cat)", "english": "C", "example": "Cat - แมว"},
        {"thai": "ดี (สำหรับ สุนัข)", "romanization": "D (for Dog)", "english": "D", "example": "Dog - สุนัข"},
        {"thai": "อี (สำหรับ ช้าง)", "romanization": "E (for Elephant)", "english": "E", "example": "Elephant - ช้าง"},
        {"thai": "เอฟ (สำหรับ ปลา)", "romanization": "F (for Fish)", "english": "F", "example": "Fish - ปลา"},
        {"thai": "จี (สำหรับ องุ่น)", "romanization": "G (for Grapes)", "english": "G", "example": "Grapes - องุ่น"},
        {"thai": "เอช (สำหรับ บ้าน)", "romanization": "H (for House)", "english": "H", "example": "House - บ้าน"},
        {"thai": "ไอ (สำหรับ ไอศกรีม)", "romanization": "I (for Ice Cream)", "english": "I", "example": "Ice Cream - ไอศกรีม"},
        {"thai": "เจ (สำหรับ กระโดด)", "romanization": "J (for Jump)", "english": "J", "example": "Jump - กระโดด"},
        {"thai": "เค (สำหรับ ว่าว)", "romanization": "K (for Kite)", "english": "K", "example": "Kite - ว่าว"},
        {"thai": "เอล (สำหรับ สิงโต)", "romanization": "L (for Lion)", "english": "L", "example": "Lion - สิงโต"},
        {"thai": "เอ็ม (สำหรับ ลิง)", "romanization": "M (for Monkey)", "english": "M", "example": "Monkey - ลิง"},
        {"thai": "เอ็น (สำหรับ รัง)", "romanization": "N (for Nest)", "english": "N", "example": "Nest - รัง"},
        {"thai": "โอ (สำหรับ ส้ม)", "romanization": "O (for Orange)", "english": "O", "example": "Orange - ส้ม"},
        {"thai": "พี (สำหรับ นกแก้ว)", "romanization": "P (for Parrot)", "english": "P", "example": "Parrot - นกแก้ว"},
        {"thai": "คิว (สำหรับ ราชินี)", "romanization": "Q (for Queen)", "english": "Q", "example": "Queen - ราชินี"},
        {"thai": "อาร์ (สำหรับ กระต่าย)", "romanization": "R (for Rabbit)", "english": "R", "example": "Rabbit - กระต่าย"},
        {"thai": "เอส (สำหรับ ดวงอาทิตย์)", "romanization": "S (for Sun)", "english": "S", "example": "Sun - ดวงอาทิตย์"},
        {"thai": "ที (สำหรับ เสือ)", "romanization": "T (for Tiger)", "english": "T", "example": "Tiger - เสือ"},
        {"thai": "ยู (สำหรับ ร่ม)", "romanization": "U (for Umbrella)", "english": "U", "example": "Umbrella - ร่ม"},
        {"thai": "วี (สำหรับ รถตู้)", "romanization": "V (for Van)", "english": "V", "example": "Van - รถตู้"},
        {"thai": "ดับเบิลยู (สำหรับ น้ำ)", "romanization": "W (for Water)", "english": "W", "example": "Water - น้ำ"},
        {"thai": "เอ็กซ์ (สำหรับ ไซโลโฟน)", "romanization": "X (for Xylophone)", "english": "X", "example": "Xylophone - ไซโลโฟน"},
        {"thai": "วาย (สำหรับ โยเกิร์ต)", "romanization": "Y (for Yogurt)", "english": "Y", "example": "Yogurt - โยเกิร์ต"},
        {"thai": "แซด (สำหรับ ม้าลาย)", "romanization": "Z (for Zebra)", "english": "Z", "example": "Zebra - ม้าลาย"}
    ]
    
    # English Numbers
    english_numbers_basic = [
        {"thai": "ศูนย์", "romanization": "Zero", "english": "0", "example": "I have zero apples - ฉันมีแอปเปิล 0 ลูก"},
        {"thai": "หนึ่ง", "romanization": "One", "english": "1", "example": "One cat - แมว 1 ตัว"},
        {"thai": "สอง", "romanization": "Two", "english": "2", "example": "Two dogs - สุนัข 2 ตัว"},
        {"thai": "สาม", "romanization": "Three", "english": "3", "example": "Three birds - นก 3 ตัว"},
        {"thai": "สี่", "romanization": "Four", "english": "4", "example": "Four books - หนังสือ 4 เล่ม"},
        {"thai": "ห้า", "romanization": "Five", "english": "5", "example": "Five fingers - นิ้ว 5 นิ้ว"},
        {"thai": "หก", "romanization": "Six", "english": "6", "example": "Six chairs - เก้าอี้ 6 ตัว"},
        {"thai": "เจ็ด", "romanization": "Seven", "english": "7", "example": "Seven days - 7 วัน"},
        {"thai": "แปด", "romanization": "Eight", "english": "8", "example": "Eight legs - ขา 8 ข้าง"},
        {"thai": "เก้า", "romanization": "Nine", "english": "9", "example": "Nine students - นักเรียน 9 คน"},
        {"thai": "สิบ", "romanization": "Ten", "english": "10", "example": "Ten pens - ปากกา 10 ด้าม"},
        {"thai": "สิบเอ็ด", "romanization": "Eleven", "english": "11", "example": "Eleven players - ผู้เล่น 11 คน"},
        {"thai": "สิบสอง", "romanization": "Twelve", "english": "12", "example": "Twelve months - 12 เดือน"},
        {"thai": "สิบสาม", "romanization": "Thirteen", "english": "13", "example": "Thirteen cookies - คุกกี้ 13 ชิ้น"},
        {"thai": "สิบสี่", "romanization": "Fourteen", "english": "14", "example": "Fourteen days - 14 วัน"},
        {"thai": "สิบห้า", "romanization": "Fifteen", "english": "15", "example": "Fifteen minutes - 15 นาที"},
        {"thai": "สิบหก", "romanization": "Sixteen", "english": "16", "example": "Sixteen years old - อายุ 16 ปี"},
        {"thai": "สิบเจ็ด", "romanization": "Seventeen", "english": "17", "example": "Seventeen apples - แอปเปิล 17 ลูก"},
        {"thai": "สิบแปด", "romanization": "Eighteen", "english": "18", "example": "Eighteen hours - 18 ชั่วโมง"},
        {"thai": "สิบเก้า", "romanization": "Nineteen", "english": "19", "example": "Nineteen people - 19 คน"},
        {"thai": "ยี่สิบ", "romanization": "Twenty", "english": "20", "example": "Twenty dollars - 20 ดอลลาร์"},
        {"thai": "สามสิบ", "romanization": "Thirty", "english": "30", "example": "Thirty minutes - 30 นาที"},
        {"thai": "สี่สิบ", "romanization": "Forty", "english": "40", "example": "Forty students - นักเรียน 40 คน"},
        {"thai": "ห้าสิบ", "romanization": "Fifty", "english": "50", "example": "Fifty pounds - 50 ปอนด์"},
        {"thai": "หกสิบ", "romanization": "Sixty", "english": "60", "example": "Sixty seconds - 60 วินาที"},
        {"thai": "เจ็ดสิบ", "romanization": "Seventy", "english": "70", "example": "Seventy percent - 70 เปอร์เซ็นต์"},
        {"thai": "แปดสิบ", "romanization": "Eighty", "english": "80", "example": "Eighty pages - 80 หน้า"},
        {"thai": "เก้าสิบ", "romanization": "Ninety", "english": "90", "example": "Ninety degrees - 90 องศา"},
        {"thai": "หนึ่งร้อย", "romanization": "One Hundred", "english": "100", "example": "One hundred meters - 100 เมตร"}
    ]
    
    # English Greetings
    english_greetings = [
        {"thai": "สวัสดี", "romanization": "Hello", "english": "Hello", "example": "Hello, how are you? - สวัสดี คุณสบายดีไหม"},
        {"thai": "สวัสดีตอนเช้า", "romanization": "Good morning", "english": "Good morning", "example": "Good morning, teacher! - สวัสดีตอนเช้า คุณครู"},
        {"thai": "สวัสดีตอนบ่าย", "romanization": "Good afternoon", "english": "Good afternoon", "example": "Good afternoon, everyone - สวัสดีตอนบ่าย ทุกคน"},
        {"thai": "สวัสดีตอนเย็น", "romanization": "Good evening", "english": "Good evening", "example": "Good evening, sir - สวัสดีตอนเย็น คุณผู้ชาย"},
        {"thai": "ราตรีสวัสดิ์", "romanization": "Good night", "english": "Good night", "example": "Good night, sleep well - ราตรีสวัสดิ์ นอนหลับฝันดี"},
        {"thai": "ลาก่อน", "romanization": "Goodbye", "english": "Goodbye", "example": "Goodbye, see you tomorrow - ลาก่อน พรุ่งนี้เจอกัน"},
        {"thai": "แล้วเจอกันใหม่", "romanization": "See you later", "english": "See you later", "example": "See you later! - แล้วเจอกันใหม่!"},
        {"thai": "ยินดีที่ได้พบคุณ", "romanization": "Nice to meet you", "english": "Nice to meet you", "example": "Nice to meet you, I'm John - ยินดีที่ได้พบคุณ ผมชื่อจอห์น"},
        {"thai": "ขอบคุณ", "romanization": "Thank you", "english": "Thank you", "example": "Thank you very much - ขอบคุณมาก"},
        {"thai": "ไม่เป็นไร", "romanization": "You're welcome", "english": "You're welcome", "example": "You're welcome! - ไม่เป็นไร"},
        {"thai": "ขอโทษ", "romanization": "Sorry", "english": "Sorry", "example": "I'm sorry - ขอโทษ"},
        {"thai": "ไม่เป็นไร", "romanization": "It's okay", "english": "It's okay", "example": "It's okay, don't worry - ไม่เป็นไร ไม่ต้องกังวล"}
    ]
    
    # English Common Phrases
    english_common_phrases = [
        {"thai": "ฉันชื่อ...", "romanization": "My name is...", "english": "My name is...", "example": "My name is Sarah - ฉันชื่อซาราห์"},
        {"thai": "คุณสบายดีไหม?", "romanization": "How are you?", "english": "How are you?", "example": "How are you today? - คุณสบายดีไหมวันนี้?"},
        {"thai": "ฉันสบายดี", "romanization": "I'm fine", "english": "I'm fine", "example": "I'm fine, thank you - ฉันสบายดี ขอบคุณ"},
        {"thai": "คุณมาจากไหน?", "romanization": "Where are you from?", "english": "Where are you from?", "example": "Where are you from? - คุณมาจากไหน?"},
        {"thai": "ฉันมาจาก...", "romanization": "I'm from...", "english": "I'm from...", "example": "I'm from Thailand - ฉันมาจากประเทศไทย"},
        {"thai": "คุณพูดภาษาอังกฤษได้ไหม?", "romanization": "Do you speak English?", "english": "Do you speak English?", "example": "Do you speak English? - คุณพูดภาษาอังกฤษได้ไหม?"},
        {"thai": "ใช่ ฉันพูดได้นิดหน่อย", "romanization": "Yes, I speak a little", "english": "Yes, I speak a little", "example": "Yes, I speak a little - ใช่ ฉันพูดได้นิดหน่อย"},
        {"thai": "คุณช่วยได้ไหม?", "romanization": "Can you help me?", "english": "Can you help me?", "example": "Can you help me, please? - คุณช่วยได้ไหม กรุณา"},
        {"thai": "นี่ราคาเท่าไหร่?", "romanization": "How much is this?", "english": "How much is this?", "example": "How much is this shirt? - เสื้อตัวนี้ราคาเท่าไหร่?"},
        {"thai": "ห้องน้ำอยู่ที่ไหน?", "romanization": "Where is the bathroom?", "english": "Where is the bathroom?", "example": "Excuse me, where is the bathroom? - ขอโทษ ห้องน้ำอยู่ที่ไหน?"},
        {"thai": "ฉันไม่เข้าใจ", "romanization": "I don't understand", "english": "I don't understand", "example": "Sorry, I don't understand - ขอโทษ ฉันไม่เข้าใจ"},
        {"thai": "พูดช้าๆ ได้ไหม?", "romanization": "Can you speak slowly?", "english": "Can you speak slowly?", "example": "Can you speak slowly, please? - พูดช้าๆ ได้ไหม กรุณา"}
    ]
    
    # English Animals
    english_animals = [
        {"thai": "สุนัข", "romanization": "Dog", "english": "Dog", "example": "I have a dog - ฉันมีสุนัข"},
        {"thai": "แมว", "romanization": "Cat", "english": "Cat", "example": "The cat is sleeping - แมวกำลังหลับ"},
        {"thai": "นก", "romanization": "Bird", "english": "Bird", "example": "Birds can fly - นกบินได้"},
        {"thai": "ปลา", "romanization": "Fish", "english": "Fish", "example": "Fish live in water - ปลาอยู่ในน้ำ"},
        {"thai": "ช้าง", "romanization": "Elephant", "english": "Elephant", "example": "Elephants are big - ช้างตัวใหญ่"},
        {"thai": "สิงโต", "romanization": "Lion", "english": "Lion", "example": "The lion is strong - สิงโตแข็งแรง"},
        {"thai": "เสือ", "romanization": "Tiger", "english": "Tiger", "example": "Tigers are dangerous - เสืออันตราย"},
        {"thai": "ลิง", "romanization": "Monkey", "english": "Monkey", "example": "Monkeys like bananas - ลิงชอบกล้วย"},
        {"thai": "กระต่าย", "romanization": "Rabbit", "english": "Rabbit", "example": "The rabbit is fast - กระต่ายเร็ว"},
        {"thai": "ม้า", "romanization": "Horse", "english": "Horse", "example": "I can ride a horse - ฉันขี่ม้าได้"},
        {"thai": "วัว", "romanization": "Cow", "english": "Cow", "example": "Cows give us milk - วัวให้นมเรา"},
        {"thai": "หมู", "romanization": "Pig", "english": "Pig", "example": "Pigs are pink - หมูสีชมพู"},
        {"thai": "ไก่", "romanization": "Chicken", "english": "Chicken", "example": "Chickens lay eggs - ไก่วางไข่"},
        {"thai": "เป็ด", "romanization": "Duck", "english": "Duck", "example": "Ducks swim well - เป็ดว่ายน้ำเก่ง"},
        {"thai": "หมี", "romanization": "Bear", "english": "Bear", "example": "Bears are big - หมีตัวใหญ่"}
    ]
    
    english_lessons = [
        {
            "title": "English Alphabet (A-Z)",
            "category": "alphabet",
            "subcategory": "letters",
            "description": "Learn all 26 English letters with Thai pronunciation",
            "items": english_alphabet_data,
            "order": 1,
            "language_mode": "learn-english"
        },
        {
            "title": "English Numbers (0-100)",
            "category": "numbers",
            "subcategory": "basic",
            "description": "Count from 0 to 100 in English",
            "items": english_numbers_basic,
            "order": 2,
            "language_mode": "learn-english"
        },
        {
            "title": "English Greetings",
            "category": "conversations",
            "subcategory": "greetings",
            "description": "Basic English greeting phrases",
            "items": english_greetings,
            "order": 3,
            "language_mode": "learn-english"
        },
        {
            "title": "Common English Phrases",
            "category": "conversations",
            "subcategory": "common",
            "description": "Essential everyday English phrases",
            "items": english_common_phrases,
            "order": 4,
            "language_mode": "learn-english"
        },
        {
            "title": "English Animals",
            "category": "vocabulary",
            "subcategory": "animals",
            "description": "Learn animal names in English",
            "items": english_animals,
            "order": 5,
            "language_mode": "learn-english"
        }
    ]
    
    # Combine Thai and English lessons
    all_lessons = lessons + english_lessons
    
    result = await db.lessons.insert_many(all_lessons)
    return {"message": "Data initialized successfully (Thai + English)", "count": len(result.inserted_ids)}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()