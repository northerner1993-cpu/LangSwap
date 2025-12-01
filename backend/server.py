from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
import os
import logging
from pathlib import Path
from bson import ObjectId
import jwt
import bcrypt

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "langswap-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# API Keys
PRIVATE_API_KEY = os.getenv("PRIVATE_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY", PRIVATE_API_KEY)
SERPAPI_ENDPOINT = os.getenv("SERPAPI_ENDPOINT", "https://serpapi.com/search")

# SerpAPI Integration
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    print("Warning: SerpAPI not available. Install 'google-search-results' package.")

# MongoDB connection with Atlas support
mongo_url = os.getenv('MONGO_URL', os.getenv('MONGODB_URI', 'mongodb://localhost:27017'))
db_name = os.getenv('DB_NAME', os.getenv('MONGODB_DB_NAME', 'langswap'))

# MongoDB client configuration for Atlas compatibility
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
    maxPoolSize=50,
    minPoolSize=10,
    retryWrites=True,
    w='majority'
)
db = client[db_name]

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Connecting to MongoDB at: {mongo_url.split('@')[-1] if '@' in mongo_url else mongo_url}")
logger.info(f"Using database: {db_name}")

# Create the main app
app = FastAPI(title="LangSwap API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    """Verify MongoDB connection on startup"""
    try:
        # Ping the database to verify connection
        await client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB")
        
        # Check if collections exist
        collections = await db.list_collection_names()
        logger.info(f"📚 Available collections: {collections}")
        
        # Initialize owner accounts if they don't exist
        try:
            await initialize_owner_accounts()
            logger.info("✅ Owner accounts initialized")
        except Exception as e:
            logger.warning(f"⚠️  Owner account initialization: {e}")
            
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        logger.error(f"MongoDB URL: {mongo_url.split('@')[-1] if '@' in mongo_url else mongo_url}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown"""
    client.close()
    logger.info("🔌 MongoDB connection closed")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        # Check MongoDB connection
        await client.admin.command('ping')
        mongo_status = "connected"
    except Exception as e:
        mongo_status = f"disconnected: {str(e)}"
        
    return {
        "status": "healthy" if mongo_status == "connected" else "unhealthy",
        "service": "langswap-api",
        "version": "1.0.0",
        "database": mongo_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "LangSwap API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "api": "/api",
            "docs": "/docs"
        }
    }

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

# Authentication Models
class UserRole(BaseModel):
    name: str
    permissions: List[str]

class User(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "user"  # user, staff, admin
    permissions: List[str] = []
    created_at: Optional[datetime] = None
    is_active: bool = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: str
    permissions: List[str]
    created_at: Optional[datetime]

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class StaffCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    permissions: List[str]

# Premium/Subscription Models
class CouponCode(BaseModel):
    code: str
    discount_percent: int
    valid_until: datetime
    max_uses: int
    used_count: int = 0
    is_active: bool = True

class Subscription(BaseModel):
    user_id: str
    plan_type: str  # "monthly", "lifetime"
    price: float
    is_active: bool = True
    purchased_at: datetime
    expires_at: Optional[datetime] = None
    coupon_used: Optional[str] = None

# Staff Access Code Models
class AccessCode(BaseModel):
    code: str
    generated_by: str  # admin user_id
    generated_by_email: str
    generated_at: datetime
    expires_at: datetime
    is_used: bool = False
    used_by: Optional[str] = None
    used_at: Optional[datetime] = None
    staff_email: Optional[str] = None
    permissions: List[str] = []

# Lesson Models
class LessonItem(BaseModel):
    thai: str
    romanization: str
    english: str
    example: Optional[str] = None
    image_url: Optional[str] = None  # Support for visual learning

class Lesson(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    title: str
    category: str  # alphabet, numbers, conversations
    subcategory: Optional[str] = None  # consonants, vowels, greetings, etc
    description: str
    items: List[LessonItem]
    order: int = 0
    language_mode: str = "learn-thai"  # "learn-thai" or "learn-english"
    thumbnail_url: Optional[str] = None  # Lesson thumbnail for better visual appeal

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

# Authentication Helper Functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Authentication Endpoints
@api_router.post("/register", response_model=TokenResponse)
async def register(user: User):
    """Register a new user"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(user.password)
    
    # Create user document
    user_doc = {
        "email": user.email,
        "username": user.username,
        "password": hashed_password,
        "role": user.role,
        "permissions": user.permissions,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    # Create access token
    access_token = create_access_token({"sub": user.email})
    
    # Return response
    user_response = UserResponse(
        id=str(user_doc["_id"]),
        email=user_doc["email"],
        username=user_doc["username"],
        role=user_doc["role"],
        permissions=user_doc["permissions"],
        created_at=user_doc["created_at"]
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.post("/login", response_model=TokenResponse)
async def login(user_login: UserLogin):
    """Login user"""
    # Find user
    user = await db.users.find_one({"email": user_login.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(user_login.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    # Create access token
    access_token = create_access_token({"sub": user["email"]})
    
    # Return response
    user_response = UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        username=user["username"],
        role=user["role"],
        permissions=user.get("permissions", []),
        created_at=user.get("created_at")
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )

@api_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        username=current_user["username"],
        role=current_user["role"],
        permissions=current_user.get("permissions", []),
        created_at=current_user.get("created_at")
    )

@api_router.post("/staff", response_model=UserResponse)
async def create_staff(staff: StaffCreate, admin_user: dict = Depends(require_admin)):
    """Create a new staff member (admin only)"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": staff.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = hash_password(staff.password)
    
    # Create staff document
    staff_doc = {
        "email": staff.email,
        "username": staff.username,
        "password": hashed_password,
        "role": "staff",
        "permissions": staff.permissions,
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = await db.users.insert_one(staff_doc)
    staff_doc["_id"] = result.inserted_id
    
    return UserResponse(
        id=str(staff_doc["_id"]),
        email=staff_doc["email"],
        username=staff_doc["username"],
        role=staff_doc["role"],
        permissions=staff_doc["permissions"],
        created_at=staff_doc["created_at"]
    )

@api_router.get("/staff", response_model=List[UserResponse])
async def get_all_staff(admin_user: dict = Depends(require_admin)):
    """Get all staff members (admin only)"""
    staff_list = []
    async for staff in db.users.find({"role": {"$in": ["staff", "admin"]}}):
        staff_list.append(UserResponse(
            id=str(staff["_id"]),
            email=staff["email"],
            username=staff["username"],
            role=staff["role"],
            permissions=staff.get("permissions", []),
            created_at=staff.get("created_at")
        ))
    return staff_list

@api_router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: str, admin_user: dict = Depends(require_admin)):
    """Delete a staff member (admin only)"""
    result = await db.users.delete_one({"_id": ObjectId(staff_id), "role": "staff"})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return {"message": "Staff member deleted successfully"}

# Staff Access Code System
@api_router.post("/access-codes/generate")
async def generate_access_code(permissions: List[str], valid_days: int = 7, admin_user: dict = Depends(require_admin)):
    """Generate a staff registration access code (admin only)"""
    import random
    import string
    
    # Generate unique 12-character code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    code = f"STAFF-{code[:4]}-{code[4:8]}-{code[8:]}"
    
    # Create access code document
    access_code_doc = {
        "code": code,
        "generated_by": str(admin_user["_id"]),
        "generated_by_email": admin_user["email"],
        "generated_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=valid_days),
        "is_used": False,
        "used_by": None,
        "used_at": None,
        "staff_email": None,
        "permissions": permissions
    }
    
    result = await db.access_codes.insert_one(access_code_doc)
    access_code_doc["_id"] = result.inserted_id
    
    # Log the generation
    await db.access_code_logs.insert_one({
        "action": "generated",
        "code": code,
        "admin_id": str(admin_user["_id"]),
        "admin_email": admin_user["email"],
        "permissions": permissions,
        "timestamp": datetime.utcnow()
    })
    
    return {
        "code": code,
        "expires_at": access_code_doc["expires_at"],
        "permissions": permissions,
        "valid_days": valid_days
    }

@api_router.post("/access-codes/validate/{code}")
async def validate_access_code(code: str):
    """Validate an access code for staff registration"""
    access_code = await db.access_codes.find_one({"code": code.upper()})
    
    if not access_code:
        raise HTTPException(status_code=404, detail="Invalid access code")
    
    if access_code.get("is_used"):
        raise HTTPException(status_code=400, detail="Access code already used")
    
    if datetime.fromisoformat(str(access_code.get("expires_at"))) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Access code expired")
    
    return {
        "valid": True,
        "permissions": access_code.get("permissions", []),
        "expires_at": access_code.get("expires_at")
    }

@api_router.post("/staff/register-with-code")
async def register_staff_with_code(email: EmailStr, username: str, password: str, access_code: str):
    """Register as staff using an access code"""
    # Validate access code
    code_doc = await db.access_codes.find_one({"code": access_code.upper()})
    
    if not code_doc:
        raise HTTPException(status_code=404, detail="Invalid access code")
    
    if code_doc.get("is_used"):
        raise HTTPException(status_code=400, detail="Access code already used")
    
    if datetime.fromisoformat(str(code_doc.get("expires_at"))) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Access code expired")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create staff account
    hashed_password = hash_password(password)
    staff_doc = {
        "email": email,
        "username": username,
        "password": hashed_password,
        "role": "staff",
        "permissions": code_doc.get("permissions", []),
        "created_at": datetime.utcnow(),
        "is_active": True,
        "registered_with_code": access_code.upper()
    }
    
    result = await db.users.insert_one(staff_doc)
    
    # Mark code as used
    await db.access_codes.update_one(
        {"code": access_code.upper()},
        {
            "$set": {
                "is_used": True,
                "used_by": str(result.inserted_id),
                "used_at": datetime.utcnow(),
                "staff_email": email
            }
        }
    )
    
    # Log the usage
    await db.access_code_logs.insert_one({
        "action": "used",
        "code": access_code.upper(),
        "staff_id": str(result.inserted_id),
        "staff_email": email,
        "timestamp": datetime.utcnow()
    })
    
    # Create access token
    access_token = create_access_token({"sub": email})
    
    return {
        "message": "Staff account created successfully",
        "access_token": access_token,
        "user": {
            "id": str(result.inserted_id),
            "email": email,
            "username": username,
            "role": "staff",
            "permissions": code_doc.get("permissions", [])
        }
    }

@api_router.get("/access-codes")
async def list_access_codes(admin_user: dict = Depends(require_admin)):
    """List all access codes (admin only)"""
    codes = []
    async for code in db.access_codes.find().sort("generated_at", -1).limit(100):
        codes.append({
            "code": code.get("code"),
            "generated_by": code.get("generated_by_email"),
            "generated_at": code.get("generated_at"),
            "expires_at": code.get("expires_at"),
            "is_used": code.get("is_used"),
            "used_by": code.get("staff_email"),
            "permissions": code.get("permissions", [])
        })
    return codes

@api_router.get("/access-codes/logs")
async def get_access_code_logs(admin_user: dict = Depends(require_admin)):
    """Get access code generation and usage logs (admin only)"""
    logs = []
    async for log in db.access_code_logs.find().sort("timestamp", -1).limit(200):
        logs.append(log)
    return logs

# SerpAPI Enhanced Search & Data Endpoints
@api_router.post("/search/language-examples")
async def search_language_examples(query: str, language: str = "thai"):
    """
    Search for real-world language examples using SerpAPI
    Enriches learning with authentic usage examples
    """
    if not SERPAPI_AVAILABLE:
        return {
            "error": "SerpAPI not available",
            "message": "Using cached examples",
            "query": query,
            "examples": []
        }
    
    try:
        # Search for language examples
        params = {
            "engine": "google",
            "q": f"{query} {language} language example usage",
            "api_key": SERPAPI_KEY,
            "num": 5
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Extract relevant information
        examples = []
        if "organic_results" in results:
            for result in results["organic_results"][:5]:
                examples.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "link": result.get("link", ""),
                    "source": "SerpAPI Google Search"
                })
        
        # Log to SerpAPI endpoint
        await log_to_serpapi({
            "action": "language_search",
            "query": query,
            "language": language,
            "results_count": len(examples),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "query": query,
            "language": language,
            "examples": examples,
            "source": "SerpAPI",
            "cached": False
        }
        
    except Exception as e:
        print(f"SerpAPI search error: {e}")
        return {
            "error": str(e),
            "query": query,
            "examples": []
        }

@api_router.post("/analytics/log")
async def log_app_analytics(data: dict):
    """
    Log app analytics data to SerpAPI endpoint
    Tracks user interactions, lesson progress, and feature usage
    """
    try:
        # Add metadata
        data["timestamp"] = datetime.utcnow().isoformat()
        data["app_version"] = "1.0.0"
        data["platform"] = data.get("platform", "unknown")
        
        # Log to SerpAPI
        await log_to_serpapi(data)
        
        # Also store in MongoDB
        await db.analytics.insert_one(data)
        
        return {
            "status": "success",
            "message": "Analytics logged successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

async def log_to_serpapi(data: dict):
    """Helper function to log data to SerpAPI endpoint"""
    import requests
    try:
        response = requests.post(
            SERPAPI_ENDPOINT,
            json=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SERPAPI_KEY}"
            },
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error logging to SerpAPI: {e}")
        return False

@api_router.post("/init-admin")
async def initialize_admin():
    """Initialize primary admin accounts with both owner emails"""
    owners = [
        {
            "email": "jakemadamson2k14@gmail.com",
            "username": "Jake Adamson",
            "password": "LangSwap2024!"
        },
        {
            "email": "Northerner1993@gmail.com",
            "username": "Co-Owner",
            "password": "LangSwap2024!"
        }
    ]
    
    created_accounts = []
    
    for owner_data in owners:
        # Check if admin already exists
        existing_admin = await db.users.find_one({"email": owner_data["email"]})
        if existing_admin:
            created_accounts.append({
                "email": owner_data["email"],
                "status": "already_exists"
            })
            continue
        
        # Create owner admin account
        admin_password = hash_password(owner_data["password"])
        admin_doc = {
            "email": owner_data["email"],
            "username": owner_data["username"],
            "password": admin_password,
            "role": "admin",
            "permissions": ["all", "owner", "global_sales_conduct", "data_protection", "staff_management"],
            "created_at": datetime.utcnow(),
            "is_active": True,
            "is_owner": True
        }
        
        await db.users.insert_one(admin_doc)
        created_accounts.append({
            "email": owner_data["email"],
            "username": owner_data["username"],
            "role": "admin - OWNER",
            "status": "created"
        })
    
    return {
        "message": "Owner accounts initialized",
        "accounts": created_accounts,
        "default_password": "LangSwap2024!",
        "note": "PLEASE CHANGE PASSWORDS IMMEDIATELY AFTER FIRST LOGIN"
    }

# Premium Subscription & Coupon Endpoints
@api_router.post("/coupons")
async def create_coupon(code: str, discount_percent: int, valid_days: int, max_uses: int, admin_user: dict = Depends(require_admin)):
    """Create a new coupon code (admin only)"""
    existing = await db.coupons.find_one({"code": code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    
    coupon_doc = {
        "code": code.upper(),
        "discount_percent": discount_percent,
        "valid_until": datetime.utcnow() + timedelta(days=valid_days),
        "max_uses": max_uses,
        "used_count": 0,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    await db.coupons.insert_one(coupon_doc)
    return {"message": "Coupon created successfully", "coupon": coupon_doc}

@api_router.get("/coupons/validate/{code}")
async def validate_coupon(code: str):
    """Validate a coupon code"""
    coupon = await db.coupons.find_one({"code": code.upper()})
    
    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid coupon code")
    
    if not coupon.get("is_active"):
        raise HTTPException(status_code=400, detail="Coupon is no longer active")
    
    if coupon.get("used_count", 0) >= coupon.get("max_uses", 0):
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")
    
    if datetime.fromisoformat(str(coupon.get("valid_until"))) < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Coupon has expired")
    
    return {
        "valid": True,
        "discount_percent": coupon.get("discount_percent"),
        "code": coupon.get("code")
    }

@api_router.post("/subscribe")
async def create_subscription(plan_type: str, coupon_code: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Purchase a subscription"""
    # Check if user already has active subscription
    existing = await db.subscriptions.find_one({
        "user_id": str(current_user["_id"]),
        "is_active": True
    })
    
    if existing:
        return {"message": "You already have an active subscription", "subscription": existing}
    
    # Pricing
    prices = {
        "monthly": 5.99,
        "lifetime": 2.99  # Special lifetime offer
    }
    
    if plan_type not in prices:
        raise HTTPException(status_code=400, detail="Invalid plan type")
    
    price = prices[plan_type]
    discount = 0
    
    # Apply coupon if provided
    if coupon_code:
        try:
            coupon = await db.coupons.find_one({"code": coupon_code.upper()})
            if coupon and coupon.get("is_active"):
                discount = coupon.get("discount_percent", 0)
                price = price * (1 - discount / 100)
                # Update coupon usage
                await db.coupons.update_one(
                    {"code": coupon_code.upper()},
                    {"$inc": {"used_count": 1}}
                )
        except:
            pass
    
    # Create subscription
    subscription_doc = {
        "user_id": str(current_user["_id"]),
        "plan_type": plan_type,
        "price": price,
        "original_price": prices[plan_type],
        "discount_applied": discount,
        "is_active": True,
        "purchased_at": datetime.utcnow(),
        "expires_at": None if plan_type == "lifetime" else datetime.utcnow() + timedelta(days=30),
        "coupon_used": coupon_code.upper() if coupon_code else None
    }
    
    result = await db.subscriptions.insert_one(subscription_doc)
    subscription_doc["_id"] = result.inserted_id
    
    return {
        "message": "Subscription activated!",
        "subscription": subscription_doc,
        "features": ["No ads", "Unlimited translations", "Offline mode", "Priority support"]
    }

@api_router.get("/my-subscription")
async def get_my_subscription(current_user: dict = Depends(get_current_user)):
    """Get current user's subscription status"""
    subscription = await db.subscriptions.find_one({
        "user_id": str(current_user["_id"]),
        "is_active": True
    })
    
    if not subscription:
        return {"has_subscription": False, "is_premium": False}
    
    # Check if expired (for monthly)
    if subscription.get("plan_type") == "monthly":
        expires_at = subscription.get("expires_at")
        if expires_at and datetime.fromisoformat(str(expires_at)) < datetime.utcnow():
            await db.subscriptions.update_one(
                {"_id": subscription["_id"]},
                {"$set": {"is_active": False}}
            )
            return {"has_subscription": False, "is_premium": False}
    
    return {
        "has_subscription": True,
        "is_premium": True,
        "plan_type": subscription.get("plan_type"),
        "purchased_at": subscription.get("purchased_at"),
        "expires_at": subscription.get("expires_at")
    }

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Thai Language Learning API"}

@api_router.get("/lessons", response_model=List[Lesson])
async def get_all_lessons(category: Optional[str] = None, language_mode: Optional[str] = None):
    query = {}
    if category:
        query["category"] = category
    if language_mode:
        query["language_mode"] = language_mode
    
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

@api_router.post("/translate")
async def translate_text(request: dict):
    """
    Enhanced translation endpoint with API key authentication
    Supports Thai ↔ English translation
    """
    text = request.get("text", "")
    source_lang = request.get("source_lang", "th")
    target_lang = request.get("target_lang", "en")
    api_key = request.get("api_key")
    
    # Verify API key if provided (for premium features)
    if api_key and api_key == PRIVATE_API_KEY:
        # Premium translation with enhanced accuracy
        premium = True
    else:
        premium = False
    
    # Enhanced translation dictionary with more phrases
    translations = {
        # Greetings
        "สวัสดี": "Hello",
        "สวัสดีครับ": "Hello (male)",
        "สวัสดีค่ะ": "Hello (female)",
        "ขอบคุณ": "Thank you",
        "ขอบคุณครับ": "Thank you (male)",
        "ขอบคุณค่ะ": "Thank you (female)",
        "ลาก่อน": "Goodbye",
        "ลาก่อนครับ": "Goodbye (male)",
        "ลาก่อนค่ะ": "Goodbye (female)",
        
        # Common phrases
        "สบายดีไหม": "How are you?",
        "สบายดี": "I'm fine",
        "ยินดีที่ได้รู้จัก": "Nice to meet you",
        "ขอโทษ": "Sorry/Excuse me",
        "ไม่เป็นไร": "It's okay/Never mind",
        "ช่วยด้วย": "Help!",
        "ฉันรักคุณ": "I love you",
        
        # Questions
        "นี่คืออะไร": "What is this?",
        "ที่ไหน": "Where?",
        "เมื่อไหร่": "When?",
        "ทำไม": "Why?",
        "อย่างไร": "How?",
        "เท่าไหร่": "How much?",
        
        # English to Thai
        "Hello": "สวัสดี",
        "Thank you": "ขอบคุณ",
        "Goodbye": "ลาก่อน",
        "How are you?": "สบายดีไหม",
        "I'm fine": "สบายดี",
        "Nice to meet you": "ยินดีที่ได้รู้จัก",
        "Sorry": "ขอโทษ",
        "Excuse me": "ขอโทษ",
        "Help!": "ช่วยด้วย",
        "I love you": "ฉันรักคุณ",
        "What is this?": "นี่คืออะไร",
        "Where?": "ที่ไหน",
        "When?": "เมื่อไหร่",
        "Why?": "ทำไม",
        "How?": "อย่างไร",
        "How much?": "เท่าไหร่"
    }
    
    # Get translation
    translated = translations.get(text, f"[Translation: {text}]")
    
    # If premium, add more context
    if premium:
        confidence = 0.98
    else:
        confidence = 0.85
    
    return {
        "original": text,
        "translated": translated,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "confidence": confidence,
        "premium": premium,
        "api_authenticated": bool(api_key == PRIVATE_API_KEY)
    }

@api_router.post("/init-data")
async def initialize_data(force: bool = False):
    """Initialize database with Thai learning content"""
    # Check if data already exists
    count = await db.lessons.count_documents({})
    if count > 0 and not force:
        return {"message": "Data already initialized", "count": count}
    
    # If force=true, clear all existing data first
    if force:
        await db.lessons.delete_many({})
        await db.progress.delete_many({})
        await db.favorites.delete_many({})
    
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
        {"thai": "ตัวอักษร A อ่านว่า เอ ใช้เริ่มคำว่า Apple (แอปเปิล)", "romanization": "A (เอ)", "english": "A", "example": "ตัวอย่าง: Apple means แอปเปิล, Ant means มด"},
        {"thai": "ตัวอักษร B อ่านว่า บี ใช้เริ่มคำว่า Ball (บอล)", "romanization": "B (บี)", "english": "B", "example": "ตัวอย่าง: Ball means ลูกบอล, Book means หนังสือ"},
        {"thai": "ตัวอักษร C อ่านว่า ซี ใช้เริ่มคำว่า Cat (แมว)", "romanization": "C (ซี)", "english": "C", "example": "ตัวอย่าง: Cat means แมว, Car means รถยนต์"},
        {"thai": "ตัวอักษร D อ่านว่า ดี ใช้เริ่มคำว่า Dog (สุนัข)", "romanization": "D (ดี)", "english": "D", "example": "ตัวอย่าง: Dog means สุนัข, Duck means เป็ด"},
        {"thai": "ตัวอักษร E อ่านว่า อี ใช้เริ่มคำว่า Elephant (ช้าง)", "romanization": "E (อี)", "english": "E", "example": "ตัวอย่าง: Elephant means ช้าง, Egg means ไข่"},
        {"thai": "ตัวอักษร F อ่านว่า เอฟ ใช้เริ่มคำว่า Fish (ปลา)", "romanization": "F (เอฟ)", "english": "F", "example": "ตัวอย่าง: Fish means ปลา, Frog means กบ"},
        {"thai": "ตัวอักษร G อ่านว่า จี ใช้เริ่มคำว่า Grapes (องุ่น)", "romanization": "G (จี)", "english": "G", "example": "ตัวอย่าง: Grapes means องุ่น, Girl means ผู้หญิง"},
        {"thai": "ตัวอักษร H อ่านว่า เอช ใช้เริ่มคำว่า House (บ้าน)", "romanization": "H (เอช)", "english": "H", "example": "ตัวอย่าง: House means บ้าน, Horse means ม้า"},
        {"thai": "ตัวอักษร I อ่านว่า ไอ ใช้เริ่มคำว่า Ice Cream (ไอศกรีม)", "romanization": "I (ไอ)", "english": "I", "example": "ตัวอย่าง: Ice Cream means ไอศกรีม, Island means เกาะ"},
        {"thai": "ตัวอักษร J อ่านว่า เจ ใช้เริ่มคำว่า Jump (กระโดด)", "romanization": "J (เจ)", "english": "J", "example": "ตัวอย่าง: Jump means กระโดด, Juice means น้ำผลไม้"},
        {"thai": "ตัวอักษร K อ่านว่า เค ใช้เริ่มคำว่า Kite (ว่าว)", "romanization": "K (เค)", "english": "K", "example": "ตัวอย่าง: Kite means ว่าว, King means กษัตริย์"},
        {"thai": "ตัวอักษร L อ่านว่า เอล ใช้เริ่มคำว่า Lion (สิงโต)", "romanization": "L (เอล)", "english": "L", "example": "ตัวอย่าง: Lion means สิงโต, Lamp means โคมไฟ"},
        {"thai": "ตัวอักษร M อ่านว่า เอ็ม ใช้เริ่มคำว่า Monkey (ลิง)", "romanization": "M (เอ็ม)", "english": "M", "example": "ตัวอย่าง: Monkey means ลิง, Moon means ดวงจันทร์"},
        {"thai": "ตัวอักษร N อ่านว่า เอ็น ใช้เริ่มคำว่า Nest (รัง)", "romanization": "N (เอ็น)", "english": "N", "example": "ตัวอย่าง: Nest means รัง, Nose means จมูก"},
        {"thai": "ตัวอักษร O อ่านว่า โอ ใช้เริ่มคำว่า Orange (ส้ม)", "romanization": "O (โอ)", "english": "O", "example": "ตัวอย่าง: Orange means ส้ม, Octopus means ปลาหมึก"},
        {"thai": "ตัวอักษร P อ่านว่า พี ใช้เริ่มคำว่า Parrot (นกแก้ว)", "romanization": "P (พี)", "english": "P", "example": "ตัวอย่าง: Parrot means นกแก้ว, Pen means ปากกา"},
        {"thai": "ตัวอักษร Q อ่านว่า คิว ใช้เริ่มคำว่า Queen (ราชินี)", "romanization": "Q (คิว)", "english": "Q", "example": "ตัวอย่าง: Queen means ราชินี, Quiet means เงียบ"},
        {"thai": "ตัวอักษร R อ่านว่า อาร์ ใช้เริ่มคำว่า Rabbit (กระต่าย)", "romanization": "R (อาร์)", "english": "R", "example": "ตัวอย่าง: Rabbit means กระต่าย, Rain means ฝน"},
        {"thai": "ตัวอักษร S อ่านว่า เอส ใช้เริ่มคำว่า Sun (ดวงอาทิตย์)", "romanization": "S (เอส)", "english": "S", "example": "ตัวอย่าง: Sun means ดวงอาทิตย์, Star means ดาว"},
        {"thai": "ตัวอักษร T อ่านว่า ที ใช้เริ่มคำว่า Tiger (เสือ)", "romanization": "T (ที)", "english": "T", "example": "ตัวอย่าง: Tiger means เสือ, Tree means ต้นไม้"},
        {"thai": "ตัวอักษร U อ่านว่า ยู ใช้เริ่มคำว่า Umbrella (ร่ม)", "romanization": "U (ยู)", "english": "U", "example": "ตัวอย่าง: Umbrella means ร่ม, Uncle means ลุง"},
        {"thai": "ตัวอักษร V อ่านว่า วี ใช้เริ่มคำว่า Van (รถตู้)", "romanization": "V (วี)", "english": "V", "example": "ตัวอย่าง: Van means รถตู้, Violin means ไวโอลิน"},
        {"thai": "ตัวอักษร W อ่านว่า ดับเบิลยู ใช้เริ่มคำว่า Water (น้ำ)", "romanization": "W (ดับเบิลยู)", "english": "W", "example": "ตัวอย่าง: Water means น้ำ, Window means หน้าต่าง"},
        {"thai": "ตัวอักษร X อ่านว่า เอ็กซ์ ใช้เริ่มคำว่า Xylophone (ไซโลโฟน)", "romanization": "X (เอ็กซ์)", "english": "X", "example": "ตัวอย่าง: Xylophone means ไซโลโฟน, X-ray means เอ็กซเรย์"},
        {"thai": "ตัวอักษร Y อ่านว่า วาย ใช้เริ่มคำว่า Yogurt (โยเกิร์ต)", "romanization": "Y (วาย)", "english": "Y", "example": "ตัวอย่าง: Yogurt means โยเกิร์ต, Yellow means สีเหลือง"},
        {"thai": "ตัวอักษร Z อ่านว่า แซด ใช้เริ่มคำว่า Zebra (ม้าลาย)", "romanization": "Z (แซด)", "english": "Z", "example": "ตัวอย่าง: Zebra means ม้าลาย, Zoo means สวนสัตว์"}
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
    
    # English Learning Songs
    english_alphabet_song = [
        {"thai": "ตอนนี้ฉันรู้ ABC แล้ว", "romanization": "Now I know my ABC", "english": "Now I know my ABC", "example": "บทเพลงตัวอักษร A-Z (คลาสสิก)"},
        {"thai": "A B C D E F G", "romanization": "A B C D E F G", "english": "A B C D E F G", "example": "บรรทัด 1: เรียนตัวอักษร 7 ตัวแรก"},
        {"thai": "H I J K L M N O P", "romanization": "H I J K L M N O P", "english": "H I J K L M N O P", "example": "บรรทัด 2: ตัวอักษร H ถึง P"},
        {"thai": "Q R S T U V", "romanization": "Q R S T U V", "english": "Q R S T U V", "example": "บรรทัด 3: ตัวอักษร Q ถึง V"},
        {"thai": "W X Y และ Z", "romanization": "W X Y and Z", "english": "W X Y and Z", "example": "บรรทัด 4: ตัวสุดท้าย W, X, Y, Z"},
        {"thai": "ตอนนี้ฉันรู้ ABC แล้ว", "romanization": "Now I know my ABC", "english": "Now I know my ABC", "example": "ท่อนซ้ำ: ตอนนี้ฉันรู้ ABC แล้ว"},
        {"thai": "ครั้งต่อไปคุณจะร้องเพลงกับฉันไหม?", "romanization": "Next time won't you sing with me?", "english": "Next time won't you sing with me?", "example": "จบเพลง: ชวนร้องด้วยกัน"}
    ]
    
    english_numbers_song = [
        {"thai": "หนึ่ง สอง ผูกรองเท้า", "romanization": "One, two, buckle my shoe", "english": "One, two, buckle my shoe", "example": "เพลงนับเลข 1-20 แบบสนุก"},
        {"thai": "สาม สี่ เคาะประตู", "romanization": "Three, four, knock at the door", "english": "Three, four, knock at the door", "example": "บรรทัด 2: เลข 3 และ 4"},
        {"thai": "ห้า หก หยิบไม้", "romanization": "Five, six, pick up sticks", "english": "Five, six, pick up sticks", "example": "บรรทัด 3: เลข 5 และ 6"},
        {"thai": "เจ็ด แปด วางให้ตรง", "romanization": "Seven, eight, lay them straight", "english": "Seven, eight, lay them straight", "example": "บรรทัด 4: เลข 7 และ 8"},
        {"thai": "เก้า สิบ ไก่ใหญ่อ้วนพี", "romanization": "Nine, ten, a big fat hen", "english": "Nine, ten, a big fat hen", "example": "บรรทัด 5: เลข 9 และ 10"},
        {"thai": "สิบเอ็ด สิบสอง ขุดและขุด", "romanization": "Eleven, twelve, dig and delve", "english": "Eleven, twelve, dig and delve", "example": "บรรทัด 6: เลข 11 และ 12"},
        {"thai": "มาร้องเพลงตัวเลขกันอีกครั้ง!", "romanization": "Let's sing the numbers song again!", "english": "Let's sing the numbers song again!", "example": "ท่อนซ้ำ: ร้องอีกครั้ง"}
    ]
    
    english_colors_song = [
        {"thai": "สีแดงและสีเหลือง สีชมพูและสีเขียว", "romanization": "Red and yellow, pink and green", "english": "Red and yellow, pink and green", "example": "เพลงสี - บรรทัดที่ 1"},
        {"thai": "สีม่วงและสีส้ม และสีน้ำเงิน", "romanization": "Purple and orange and blue", "english": "Purple and orange and blue", "example": "เพลงสี - บรรทัดที่ 2"},
        {"thai": "ฉันสามารถร้องเพลงสีรุ้งได้", "romanization": "I can sing a rainbow", "english": "I can sing a rainbow", "example": "ท่อนซ้ำ: ฉันร้องเพลงสีรุ้งได้"},
        {"thai": "ร้องเพลงสีรุ้งด้วย", "romanization": "Sing a rainbow too", "english": "Sing a rainbow too", "example": "คุณก็ร้องได้เหมือนกัน"},
        {"thai": "ฟังด้วยหูของคุณ มองด้วยตาของคุณ", "romanization": "Listen with your ears, look with your eyes", "english": "Listen with your ears, look with your eyes", "example": "บรรทัดที่ 5: ใช้ประสาทสัมผัส"},
        {"thai": "และร้องเพลงทุกอย่างที่อยู่ข้างใน", "romanization": "And sing everything you find", "english": "And sing everything you find", "example": "ร้องเพลงทุกสิ่งที่เห็น"}
    ]
    
    # Additional English Lessons (Mirrored Content)
    
    # English Colors
    english_colors = [
        {"thai": "สี", "romanization": "Color", "english": "Color", "example": "What color is it? - มันเป็นสีอะไร?"},
        {"thai": "แดง", "romanization": "Red", "english": "Red", "example": "The apple is red - แอปเปิลสีแดง"},
        {"thai": "น้ำเงิน", "romanization": "Blue", "english": "Blue", "example": "The sky is blue - ท้องฟ้าสีน้ำเงิน"},
        {"thai": "เขียว", "romanization": "Green", "english": "Green", "example": "Trees are green - ต้นไม้สีเขียว"},
        {"thai": "เหลือง", "romanization": "Yellow", "english": "Yellow", "example": "Bananas are yellow - กล้วยสีเหลือง"},
        {"thai": "ส้ม", "romanization": "Orange", "english": "Orange", "example": "The orange is orange - ส้มสีส้ม"},
        {"thai": "ม่วง", "romanization": "Purple", "english": "Purple", "example": "Grapes are purple - องุ่นสีม่วง"},
        {"thai": "ชมพู", "romanization": "Pink", "english": "Pink", "example": "Pink is pretty - สีชมพูสวย"},
        {"thai": "ดำ", "romanization": "Black", "english": "Black", "example": "Black shoes - รองเท้าสีดำ"},
        {"thai": "ขาว", "romanization": "White", "english": "White", "example": "White shirt - เสื้อสีขาว"},
        {"thai": "เทา", "romanization": "Gray", "english": "Gray", "example": "Gray clouds - เมฆสีเทา"},
        {"thai": "น้ำตาล", "romanization": "Brown", "english": "Brown", "example": "Brown dog - สุนัขสีน้ำตาล"}
    ]
    
    # English Family Members
    english_family = [
        {"thai": "ครอบครัว", "romanization": "Family", "english": "Family", "example": "My family - ครอบครัวของฉัน"},
        {"thai": "พ่อ", "romanization": "Father", "english": "Father", "example": "My father - พ่อของฉัน"},
        {"thai": "แม่", "romanization": "Mother", "english": "Mother", "example": "My mother - แม่ของฉัน"},
        {"thai": "พี่ชาย", "romanization": "Older brother", "english": "Older brother", "example": "My older brother - พี่ชายของฉัน"},
        {"thai": "พี่สาว", "romanization": "Older sister", "english": "Older sister", "example": "My older sister - พี่สาวของฉัน"},
        {"thai": "น้องชาย", "romanization": "Younger brother", "english": "Younger brother", "example": "My younger brother - น้องชายของฉัน"},
        {"thai": "น้องสาว", "romanization": "Younger sister", "english": "Younger sister", "example": "My younger sister - น้องสาวของฉัน"},
        {"thai": "ปู่", "romanization": "Grandfather", "english": "Grandfather", "example": "My grandfather - ปู่ของฉัน"},
        {"thai": "ย่า", "romanization": "Grandmother", "english": "Grandmother", "example": "My grandmother - ย่าของฉัน"},
        {"thai": "ลูก", "romanization": "Child", "english": "Child", "example": "My child - ลูกของฉัน"}
    ]
    
    # English Days of the Week
    english_days = [
        {"thai": "วัน", "romanization": "Day", "english": "Day", "example": "What day is it? - วันนี้วันอะไร?"},
        {"thai": "จันทร์", "romanization": "Monday", "english": "Monday", "example": "I work on Monday - ฉันทำงานวันจันทร์"},
        {"thai": "อังคาร", "romanization": "Tuesday", "english": "Tuesday", "example": "Tuesday is next - วันอังคารวันถัดไป"},
        {"thai": "พุธ", "romanization": "Wednesday", "english": "Wednesday", "example": "Wednesday morning - เช้าวันพุธ"},
        {"thai": "พฤหัสบดี", "romanization": "Thursday", "english": "Thursday", "example": "Thursday evening - เย็นวันพฤหัสบดี"},
        {"thai": "ศุกร์", "romanization": "Friday", "english": "Friday", "example": "Friday is fun day - ว��นศุกร์วันสนุก"},
        {"thai": "เสาร์", "romanization": "Saturday", "english": "Saturday", "example": "Saturday weekend - วันเสาร์วันหยุด"},
        {"thai": "อาทิตย์", "romanization": "Sunday", "english": "Sunday", "example": "Sunday rest day - วันอาทิตย์พักผ่อน"},
        {"thai": "วันนี้", "romanization": "Today", "english": "Today", "example": "Today is good - วันนี้ดี"},
        {"thai": "เมื่อวาน", "romanization": "Yesterday", "english": "Yesterday", "example": "Yesterday was fun - เมื่อวานสนุก"},
        {"thai": "พรุ่งนี้", "romanization": "Tomorrow", "english": "Tomorrow", "example": "See you tomorrow - พรุ่งนี้เจอกัน"}
    ]
    
    # Daily Conversation - Restaurant & Food (Beginner)
    daily_restaurant_beginner = [
        {"thai": "ฉันหิวแล้ว", "romanization": "chan hiu laew / I'm hungry", "english": "I'm hungry", "example": "Time to eat - เวลากินข้าว"},
        {"thai": "อร่อย", "romanization": "aroi / Delicious", "english": "Delicious", "example": "This is delicious - อันนี้อร่อย"},
        {"thai": "น้ำ", "romanization": "nam / Water", "english": "Water", "example": "I want water - ฉันต้องการน้ำ"},
        {"thai": "กาแฟ", "romanization": "ga-fae / Coffee", "english": "Coffee", "example": "Hot coffee - กาแฟร้อน"},
        {"thai": "เมนู", "romanization": "menu / Menu", "english": "Menu", "example": "May I see the menu? - ขอดูเมนูได้ไหม"},
        {"thai": "บิล", "romanization": "bin / Bill", "english": "Bill/Check", "example": "Check please - เช็คบิลด้วย"},
        {"thai": "ราคา", "romanization": "ra-ka / Price", "english": "Price", "example": "How much? - ราคาเท่าไหร่"},
        {"thai": "แพง", "romanization": "phaeng / Expensive", "english": "Expensive", "example": "Too expensive - แพงเกินไป"},
        {"thai": "ถูก", "romanization": "thuuk / Cheap", "english": "Cheap", "example": "Very cheap - ถูกมาก"},
        {"thai": "อิ่ม", "romanization": "im / Full", "english": "Full (stomach)", "example": "I'm full - ฉันอิ่มแล้ว"}
    ]
    
    # Daily Conversation - Shopping (Beginner)
    daily_shopping_beginner = [
        {"thai": "ซื้อ", "romanization": "sue / Buy", "english": "Buy", "example": "I want to buy - ฉันอยากซื้อ"},
        {"thai": "ขาย", "romanization": "khai / Sell", "english": "Sell", "example": "Do you sell? - คุณขายไหม"},
        {"thai": "ลด", "romanization": "lot / Discount", "english": "Discount", "example": "Is there a discount? - มีส่วนลดไหม"},
        {"thai": "ใหม่", "romanization": "mai / New", "english": "New", "example": "Brand new - ใหม่เอี่ยม"},
        {"thai": "เก่า", "romanization": "gao / Old", "english": "Old", "example": "Used/old - ของเก่า"},
        {"thai": "สวย", "romanization": "suay / Beautiful", "english": "Beautiful", "example": "Very beautiful - สวยมาก"},
        {"thai": "ใหญ่", "romanization": "yai / Big", "english": "Big", "example": "Too big - ใหญ่เกินไป"},
        {"thai": "เล็ก", "romanization": "lek / Small", "english": "Small", "example": "Too small - เล็กเกินไป"},
        {"thai": "พอดี", "romanization": "pho-di / Just right", "english": "Just right/Fits", "example": "Perfect fit - พอดีเลย"},
        {"thai": "ลอง", "romanization": "long / Try", "english": "Try", "example": "Can I try? - ลองได้ไหม"}
    ]
    
    # Daily Conversation - Transportation (Beginner)
    daily_transport_beginner = [
        {"thai": "ไป", "romanization": "pai / Go", "english": "Go", "example": "I want to go - ฉันอยากไป"},
        {"thai": "มา", "romanization": "ma / Come", "english": "Come", "example": "Come here - มานี่"},
        {"thai": "รถแท็กซี่", "romanization": "rot taxi / Taxi", "english": "Taxi", "example": "Call a taxi - เรียกแท็กซี่"},
        {"thai": "รถไฟฟ้า", "romanization": "rot fai fa / Sky train", "english": "Sky train/BTS", "example": "Take the BTS - นั่งรถไฟฟ้า"},
        {"thai": "รถเมล์", "romanization": "rot mae / Bus", "english": "Bus", "example": "Bus stop - ป้ายรถเมล์"},
        {"thai": "สถานี", "romanization": "sa-tha-ni / Station", "english": "Station", "example": "Train station - สถานีรถไฟ"},
        {"thai": "ที่นี่", "romanization": "thi-ni / Here", "english": "Here", "example": "Stop here - จอดที่นี่"},
        {"thai": "ที่นั่น", "romanization": "thi-nan / There", "english": "There", "example": "Over there - ที่นั่น"},
        {"thai": "ใกล้", "romanization": "glai / Near", "english": "Near/Close", "example": "Very close - ใกล้มาก"},
        {"thai": "ไกล", "romanization": "glai / Far", "english": "Far", "example": "Too far - ไกลเกินไป"}
    ]
    
    # Weather & Time - Intermediate
    daily_weather_intermediate = [
        {"thai": "อากาศ", "romanization": "a-gat / Weather", "english": "Weather", "example": "The weather today - อากาศวันนี้"},
        {"thai": "ร้อน", "romanization": "ron / Hot", "english": "Hot", "example": "Very hot - ร้อนมาก"},
        {"thai": "หนาว", "romanization": "nao / Cold", "english": "Cold", "example": "Cold weather - อากาศหนาว"},
        {"thai": "ฝน", "romanization": "fon / Rain", "english": "Rain", "example": "It's raining - ฝนตก"},
        {"thai": "แดด", "romanization": "daet / Sun", "english": "Sun/Sunny", "example": "Sunny day - วันแดดดี"},
        {"thai": "เมฆ", "romanization": "mek / Cloud", "english": "Cloud", "example": "Cloudy - มีเมฆมาก"},
        {"thai": "ลม", "romanization": "lom / Wind", "english": "Wind", "example": "Windy - ลมแรง"},
        {"thai": "ตอนเช้า", "romanization": "ton chao / Morning", "english": "Morning", "example": "Good morning - สวัสดีตอนเช้า"},
        {"thai": "ตอนเที่ยง", "romanization": "ton thiang / Noon", "english": "Noon", "example": "At noon - ตอนเที่ยง"},
        {"thai": "ตอนเย็น", "romanization": "ton yen / Evening", "english": "Evening", "example": "This evening - เย็นนี้"}
    ]
    
    # Emotions & Feelings - Intermediate  
    daily_feelings_intermediate = [
        {"thai": "มีความสุข", "romanization": "mi kwam suk / Happy", "english": "Happy", "example": "I'm happy - ฉันมีความสุข"},
        {"thai": "เศร้า", "romanization": "sao / Sad", "english": "Sad", "example": "Feeling sad - รู้สึกเศร้า"},
        {"thai": "โกรธ", "romanization": "grot / Angry", "english": "Angry", "example": "I'm angry - ฉันโกรธ"},
        {"thai": "ตื่นเต้น", "romanization": "tuen ten / Excited", "english": "Excited", "example": "Very excited - ตื่นเต้นมาก"},
        {"thai": "เหนื่อย", "romanization": "nuey / Tired", "english": "Tired", "example": "I'm tired - ฉันเหนื่อย"},
        {"thai": "ง่วง", "romanization": "nguang / Sleepy", "english": "Sleepy", "example": "Feel sleepy - รู้สึกง่วง"},
        {"thai": "กลัว", "romanization": "glua / Scared", "english": "Scared/Afraid", "example": "I'm scared - ฉันกลัว"},
        {"thai": "แปลกใจ", "romanization": "plaek jai / Surprised", "english": "Surprised", "example": "Very surprised - แปลกใจมาก"},
        {"thai": "เบื่อ", "romanization": "buea / Bored", "english": "Bored", "example": "I'm bored - ฉันเบื่อ"},
        {"thai": "รัก", "romanization": "rak / Love", "english": "Love", "example": "I love - ฉันรัก"}
    ]
    
    # Work & Office - Intermediate
    daily_work_intermediate = [
        {"thai": "ทำงาน", "romanization": "tham ngan / Work", "english": "Work", "example": "I work at - ฉันทำงานที่"},
        {"thai": "สำนักงาน", "romanization": "sam-nak-ngan / Office", "english": "Office", "example": "Go to office - ไปออฟฟิศ"},
        {"thai": "ประชุม", "romanization": "pra-chum / Meeting", "english": "Meeting", "example": "In a meeting - อยู่ในประชุม"},
        {"thai": "คอมพิวเตอร์", "romanization": "com / Computer", "english": "Computer", "example": "Use computer - ใช้คอมพิวเตอร์"},
        {"thai": "อีเมล", "romanization": "email / Email", "english": "Email", "example": "Send email - ส่งอีเมล"},
        {"thai": "โทรศัพท์", "romanization": "tho-ra-sap / Telephone", "english": "Telephone", "example": "Phone call - โทรศัพท์"},
        {"thai": "เอกสาร", "romanization": "aek-ka-san / Document", "english": "Document", "example": "Important document - เอกสารสำคัญ"},
        {"thai": "นัดหมาย", "romanization": "nat mai / Appointment", "english": "Appointment", "example": "Make appointment - นัดหมาย"},
        {"thai": "เจ้านาย", "romanization": "jao nai / Boss", "english": "Boss", "example": "My boss - เจ้านายของฉัน"},
        {"thai": "เพื่อนร่วมงาน", "romanization": "phuean ruam ngan / Colleague", "english": "Colleague", "example": "My colleague - เพื่อนร่วมงาน"}
    ]
    
    # Expanded Household Items (100+ items for both Thai and English)
    household_expanded = [
        {"thai": "ห้องน้ำ", "romanization": "hong-naam / Bathroom", "english": "Bathroom", "example": "I need the bathroom - ฉันต้องการห้องน้ำ"},
        {"thai": "ห้องครัว", "romanization": "hong-khrua / Kitchen", "english": "Kitchen", "example": "Cooking in kitchen - ทำอาหารในครัว"},
        {"thai": "ห้องนอน", "romanization": "hong-norn / Bedroom", "english": "Bedroom", "example": "Sleep in bedroom - นอนในห้องนอน"},
        {"thai": "ห้องนั่งเล่น", "romanization": "hong-nang-len / Living room", "english": "Living room", "example": "Relax in living room - พักผ่อนในห้องนั่งเล่น"},
        {"thai": "โซฟา", "romanization": "sofa / Sofa", "english": "Sofa", "example": "Sit on sofa - นั่งบนโซฟา"},
        {"thai": "พรม", "romanization": "phrom / Carpet", "english": "Carpet", "example": "Soft carpet - พรมนุ่ม"},
        {"thai": "ม่าน", "romanization": "maan / Curtain", "english": "Curtain", "example": "Close curtains - ปิดม่าน"},
        {"thai": "กระจกเงา", "romanization": "gra-jok-ngao / Mirror", "english": "Mirror", "example": "Look in mirror - ดูกระจกเงา"},
        {"thai": "นาฬิกา", "romanization": "naa-li-gaa / Clock", "english": "Clock", "example": "Check the clock - ดูนาฬิกา"},
        {"thai": "รูปภาพ", "romanization": "ruup-phaap / Picture", "english": "Picture", "example": "Hang picture - แขวนรูปภาพ"},
        {"thai": "หนังสือ", "romanization": "nang-sue / Book", "english": "Book", "example": "Read a book - อ่านหนังสือ"},
        {"thai": "ชั้นหนังสือ", "romanization": "chan-nang-sue / Bookshelf", "english": "Bookshelf", "example": "Books on bookshelf - หนังสือบนชั้น"},
        {"thai": "เครื่องคอมพิวเตอร์", "romanization": "khrueng-com / Computer", "english": "Computer", "example": "Work on computer - ทำงานกับคอมพิวเตอร์"},
        {"thai": "แล็ปท็อป", "romanization": "laptop / Laptop", "english": "Laptop", "example": "Use laptop - ใช้แล็ปท็อป"},
        {"thai": "โทรศัพท์", "romanization": "tho-ra-sap / Telephone", "english": "Telephone", "example": "Answer telephone - รับโทรศัพท์"},
        {"thai": "มือถือ", "romanization": "mue-thue / Mobile phone", "english": "Mobile phone", "example": "Call on mobile - โทรมือถือ"},
        {"thai": "เตารีด", "romanization": "tao-riit / Iron", "english": "Iron", "example": "Iron clothes - รีดเสื้อผ้า"},
        {"thai": "เครื่องซักผ้า", "romanization": "khrueng-sak-phaa / Washing machine", "english": "Washing machine", "example": "Wash clothes - ซักเสื้อผ้า"},
        {"thai": "เครื่องอบผ้า", "romanization": "khrueng-op-phaa / Dryer", "english": "Dryer", "example": "Dry clothes - อบผ้า"},
        {"thai": "ไม้กวาด", "romanization": "mai-gwaat / Broom", "english": "Broom", "example": "Sweep floor - กวาดพื้น"},
        {"thai": "ถังขยะ", "romanization": "thang-kha-ya / Trash can", "english": "Trash can", "example": "Throw in trash - ทิ้งขยะ"},
        {"thai": "เครื่องดูดฝุ่น", "romanization": "khrueng-duut-fun / Vacuum cleaner", "english": "Vacuum cleaner", "example": "Vacuum carpet - ดูดฝุ่นพรม"}
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
        },
        {
            "title": "English Colors",
            "category": "vocabulary",
            "subcategory": "colors",
            "description": "Learn English colors with examples",
            "items": english_colors,
            "order": 6,
            "language_mode": "learn-english"
        },
        {
            "title": "English Family Members",
            "category": "vocabulary",
            "subcategory": "family",
            "description": "English words for family relationships",
            "items": english_family,
            "order": 7,
            "language_mode": "learn-english"
        },
        {
            "title": "English Days of the Week",
            "category": "time",
            "subcategory": "days",
            "description": "Learn English days and time expressions",
            "items": english_days,
            "order": 8,
            "language_mode": "learn-english"
        },
        {
            "title": "English Household Items (100+ items)",
            "category": "vocabulary",
            "subcategory": "household",
            "description": "Common items found at home in English",
            "items": household_expanded,
            "order": 9,
            "language_mode": "learn-english"
        },
        {
            "title": "ABC Song",
            "category": "songs",
            "subcategory": "alphabet",
            "description": "Learn English alphabet through the classic ABC song",
            "items": english_alphabet_song,
            "order": 10,
            "language_mode": "learn-english"
        },
        {
            "title": "Numbers Song (1-12)",
            "category": "songs",
            "subcategory": "numbers",
            "description": "Fun English counting song with rhymes",
            "items": english_numbers_song,
            "order": 11,
            "language_mode": "learn-english"
        },
        {
            "title": "Colors Song (Rainbow)",
            "category": "songs",
            "subcategory": "colors",
            "description": "Learn colors in English through the Rainbow song",
            "items": english_colors_song,
            "order": 12,
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