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

@api_router.post("/init-data")
async def initialize_data():
    """Initialize database with Thai learning content"""
    # Check if data already exists
    count = await db.lessons.count_documents({})
    if count > 0:
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
    
    # Numbers
    numbers_data = [
        {"thai": "๐", "romanization": "soon", "english": "0", "example": "zero"},
        {"thai": "๑", "romanization": "neung", "english": "1", "example": "one"},
        {"thai": "๒", "romanization": "song", "english": "2", "example": "two"},
        {"thai": "๓", "romanization": "saam", "english": "3", "example": "three"},
        {"thai": "๔", "romanization": "sii", "english": "4", "example": "four"},
        {"thai": "๕", "romanization": "haa", "english": "5", "example": "five"},
        {"thai": "๖", "romanization": "hok", "english": "6", "example": "six"},
        {"thai": "๗", "romanization": "jet", "english": "7", "example": "seven"},
        {"thai": "๘", "romanization": "bpaet", "english": "8", "example": "eight"},
        {"thai": "๙", "romanization": "gao", "english": "9", "example": "nine"},
        {"thai": "สิบ", "romanization": "sip", "english": "10", "example": "ten"},
        {"thai": "ยี่สิบ", "romanization": "yii-sip", "english": "20", "example": "twenty"},
        {"thai": "สามสิบ", "romanization": "saam-sip", "english": "30", "example": "thirty"},
        {"thai": "สี่สิบ", "romanization": "sii-sip", "english": "40", "example": "forty"},
        {"thai": "ห้าสิบ", "romanization": "haa-sip", "english": "50", "example": "fifty"},
        {"thai": "หกสิบ", "romanization": "hok-sip", "english": "60", "example": "sixty"},
        {"thai": "เจ็ดสิบ", "romanization": "jet-sip", "english": "70", "example": "seventy"},
        {"thai": "แปดสิบ", "romanization": "bpaet-sip", "english": "80", "example": "eighty"},
        {"thai": "เก้าสิบ", "romanization": "gao-sip", "english": "90", "example": "ninety"},
        {"thai": "หนึ่งร้อย", "romanization": "neung-roi", "english": "100", "example": "one hundred"}
    ]
    
    # Greetings
    greetings_data = [
        {"thai": "สวัสดี", "romanization": "sawatdee", "english": "Hello / Goodbye", "example": "สวัสดีครับ (male) / สวัสดีค่ะ (female)"},
        {"thai": "สบายดีไหม", "romanization": "sabai dee mai", "english": "How are you?", "example": "คุณสบายดีไหม"},
        {"thai": "สบายดี", "romanization": "sabai dee", "english": "I'm fine", "example": "สบายดีครับ"},
        {"thai": "ขอบคุณ", "romanization": "khob khun", "english": "Thank you", "example": "ขอบคุณมากครับ (thank you very much)"},
        {"thai": "ขอโทษ", "romanization": "khor thot", "english": "Sorry / Excuse me", "example": "ขอโทษครับ"},
        {"thai": "ไม่เป็นไร", "romanization": "mai pen rai", "english": "You're welcome / No problem", "example": "ไม่เป็นไรค่ะ"},
        {"thai": "ยินดีที่ได้รู้จัก", "romanization": "yin dee tii dai ruu jak", "english": "Nice to meet you", "example": "ยินดีที่ได้รู้จักครับ"},
        {"thai": "ลาก่อน", "romanization": "laa gorn", "english": "Goodbye", "example": "ลาก่อนค่ะ"},
        {"thai": "ราตรีสวัสดิ์", "romanization": "raat-rii sawat", "english": "Good night", "example": "ราตรีสวัสดิ์ครับ"},
        {"thai": "ฉันชื่อ...", "romanization": "chan chuu...", "english": "My name is...", "example": "ฉันชื่อจอห์น"},
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
            "title": "Numbers",
            "category": "numbers",
            "subcategory": "basic",
            "description": "Learn Thai numbers from 0 to 100",
            "items": numbers_data,
            "order": 3
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
            "order": 7
        }
    ]
    
    result = await db.lessons.insert_many(lessons)
    return {"message": "Data initialized successfully", "count": len(result.inserted_ids)}

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