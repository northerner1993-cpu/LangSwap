#!/usr/bin/env python3
"""
Thai Language Learning App - Backend API Tests
Tests all backend endpoints according to the sequential test plan.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('EXPO_PUBLIC_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
    return "https://langswap-4.preview.emergentagent.com"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

class ThaiLearningAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.lesson_ids = []
        self.user_id = "test_user_thai_2024"
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    def test_1_data_initialization(self):
        """Test 1: Data Initialization - POST /api/init-data"""
        print("=== Test 1: Data Initialization ===")
        
        try:
            response = self.session.post(f"{API_URL}/init-data")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if data was initialized or already exists
                if "count" in data:
                    expected_lessons = 7
                    if isinstance(data.get("count"), int) and data["count"] >= expected_lessons:
                        self.log_test(
                            "Data Initialization", 
                            True, 
                            f"Successfully initialized/verified {data['count']} lessons. Message: {data.get('message', '')}"
                        )
                    else:
                        self.log_test(
                            "Data Initialization", 
                            False, 
                            f"Expected at least {expected_lessons} lessons, got {data.get('count')}", 
                            data
                        )
                else:
                    self.log_test(
                        "Data Initialization", 
                        False, 
                        "Response missing 'count' field", 
                        data
                    )
            else:
                self.log_test(
                    "Data Initialization", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Data Initialization", False, f"Exception: {str(e)}")

    def test_2_get_all_lessons(self):
        """Test 2: Get All Lessons - GET /api/lessons"""
        print("=== Test 2: Get All Lessons ===")
        
        try:
            response = self.session.get(f"{API_URL}/lessons")
            
            if response.status_code == 200:
                lessons = response.json()
                
                if isinstance(lessons, list) and len(lessons) >= 7:
                    # Store lesson IDs for later tests
                    self.lesson_ids = [lesson.get("id") or lesson.get("_id") for lesson in lessons]
                    
                    # Verify lesson structure
                    required_fields = ["title", "category", "description", "items"]
                    valid_lessons = 0
                    categories_found = set()
                    
                    for lesson in lessons:
                        if all(field in lesson for field in required_fields):
                            valid_lessons += 1
                            categories_found.add(lesson["category"])
                            
                            # Verify items structure
                            if isinstance(lesson["items"], list) and len(lesson["items"]) > 0:
                                item = lesson["items"][0]
                                if not all(field in item for field in ["thai", "romanization", "english"]):
                                    self.log_test(
                                        "Get All Lessons - Item Structure", 
                                        False, 
                                        f"Lesson '{lesson['title']}' has invalid item structure"
                                    )
                    
                    expected_categories = {"alphabet", "numbers", "conversations"}
                    if expected_categories.issubset(categories_found):
                        self.log_test(
                            "Get All Lessons", 
                            True, 
                            f"Retrieved {len(lessons)} lessons with all expected categories: {categories_found}"
                        )
                    else:
                        missing = expected_categories - categories_found
                        self.log_test(
                            "Get All Lessons", 
                            False, 
                            f"Missing categories: {missing}. Found: {categories_found}"
                        )
                else:
                    self.log_test(
                        "Get All Lessons", 
                        False, 
                        f"Expected at least 7 lessons, got {len(lessons) if isinstance(lessons, list) else 'non-list'}", 
                        lessons
                    )
            else:
                self.log_test(
                    "Get All Lessons", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Get All Lessons", False, f"Exception: {str(e)}")

    def test_3_get_lessons_by_category(self):
        """Test 3: Get Lessons by Category - GET /api/lessons?category=X"""
        print("=== Test 3: Get Lessons by Category ===")
        
        categories = ["alphabet", "numbers", "conversations"]
        
        for category in categories:
            try:
                response = self.session.get(f"{API_URL}/lessons", params={"category": category})
                
                if response.status_code == 200:
                    lessons = response.json()
                    
                    if isinstance(lessons, list):
                        # Verify all lessons belong to the requested category
                        valid_category = all(lesson.get("category") == category for lesson in lessons)
                        
                        if valid_category and len(lessons) > 0:
                            expected_counts = {
                                "alphabet": 2,  # consonants + vowels
                                "numbers": 1,   # numbers
                                "conversations": 4  # greetings + common + dining + travel
                            }
                            
                            if len(lessons) == expected_counts.get(category, 1):
                                self.log_test(
                                    f"Get Lessons by Category - {category}", 
                                    True, 
                                    f"Retrieved {len(lessons)} lessons for category '{category}'"
                                )
                            else:
                                self.log_test(
                                    f"Get Lessons by Category - {category}", 
                                    False, 
                                    f"Expected {expected_counts.get(category, 1)} lessons for '{category}', got {len(lessons)}"
                                )
                        else:
                            self.log_test(
                                f"Get Lessons by Category - {category}", 
                                False, 
                                f"Invalid category filtering or no lessons found for '{category}'"
                            )
                    else:
                        self.log_test(
                            f"Get Lessons by Category - {category}", 
                            False, 
                            "Response is not a list", 
                            lessons
                        )
                else:
                    self.log_test(
                        f"Get Lessons by Category - {category}", 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test(f"Get Lessons by Category - {category}", False, f"Exception: {str(e)}")

    def test_4_get_lesson_by_id(self):
        """Test 4: Get Lesson by ID - GET /api/lessons/{lesson_id}"""
        print("=== Test 4: Get Lesson by ID ===")
        
        if not self.lesson_ids:
            self.log_test("Get Lesson by ID", False, "No lesson IDs available from previous test")
            return
            
        # Test valid lesson ID
        lesson_id = self.lesson_ids[0]
        try:
            response = self.session.get(f"{API_URL}/lessons/{lesson_id}")
            
            if response.status_code == 200:
                lesson = response.json()
                
                required_fields = ["title", "category", "description", "items"]
                if all(field in lesson for field in required_fields):
                    self.log_test(
                        "Get Lesson by ID - Valid ID", 
                        True, 
                        f"Retrieved lesson: '{lesson['title']}' with {len(lesson['items'])} items"
                    )
                else:
                    missing_fields = [field for field in required_fields if field not in lesson]
                    self.log_test(
                        "Get Lesson by ID - Valid ID", 
                        False, 
                        f"Missing required fields: {missing_fields}", 
                        lesson
                    )
            else:
                self.log_test(
                    "Get Lesson by ID - Valid ID", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Get Lesson by ID - Valid ID", False, f"Exception: {str(e)}")
        
        # Test invalid lesson ID
        try:
            invalid_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format but non-existent
            response = self.session.get(f"{API_URL}/lessons/{invalid_id}")
            
            if response.status_code == 404:
                self.log_test(
                    "Get Lesson by ID - Invalid ID", 
                    True, 
                    "Correctly returned 404 for non-existent lesson ID"
                )
            else:
                self.log_test(
                    "Get Lesson by ID - Invalid ID", 
                    False, 
                    f"Expected 404, got HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Get Lesson by ID - Invalid ID", False, f"Exception: {str(e)}")

    def test_5_progress_tracking(self):
        """Test 5: Progress Tracking - POST /api/progress and GET /api/progress"""
        print("=== Test 5: Progress Tracking ===")
        
        if not self.lesson_ids:
            self.log_test("Progress Tracking", False, "No lesson IDs available for testing")
            return
            
        lesson_id = self.lesson_ids[0]
        
        # Test saving progress
        progress_data = {
            "user_id": self.user_id,
            "lesson_id": lesson_id,
            "completed": True,
            "completed_items": [0, 1, 2, 3, 4]
        }
        
        try:
            response = self.session.post(f"{API_URL}/progress", json=progress_data)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    self.log_test(
                        "Progress Tracking - Save Progress", 
                        True, 
                        f"Successfully saved progress. Modified: {result.get('modified', 'N/A')}"
                    )
                else:
                    self.log_test(
                        "Progress Tracking - Save Progress", 
                        False, 
                        "Response indicates failure", 
                        result
                    )
            else:
                self.log_test(
                    "Progress Tracking - Save Progress", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Progress Tracking - Save Progress", False, f"Exception: {str(e)}")
        
        # Test retrieving progress
        try:
            response = self.session.get(f"{API_URL}/progress", params={"user_id": self.user_id})
            
            if response.status_code == 200:
                progress_list = response.json()
                
                if isinstance(progress_list, list):
                    # Find our saved progress
                    our_progress = next((p for p in progress_list if p.get("lesson_id") == lesson_id), None)
                    
                    if our_progress:
                        expected_items = progress_data["completed_items"]
                        actual_items = our_progress.get("completed_items", [])
                        
                        if actual_items == expected_items:
                            self.log_test(
                                "Progress Tracking - Retrieve Progress", 
                                True, 
                                f"Successfully retrieved progress with {len(actual_items)} completed items"
                            )
                        else:
                            self.log_test(
                                "Progress Tracking - Retrieve Progress", 
                                False, 
                                f"Progress mismatch. Expected: {expected_items}, Got: {actual_items}"
                            )
                    else:
                        self.log_test(
                            "Progress Tracking - Retrieve Progress", 
                            False, 
                            f"Saved progress not found in response. Total progress entries: {len(progress_list)}"
                        )
                else:
                    self.log_test(
                        "Progress Tracking - Retrieve Progress", 
                        False, 
                        "Response is not a list", 
                        progress_list
                    )
            else:
                self.log_test(
                    "Progress Tracking - Retrieve Progress", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Progress Tracking - Retrieve Progress", False, f"Exception: {str(e)}")
        
        # Test upsert functionality (update existing progress)
        updated_progress = {
            "user_id": self.user_id,
            "lesson_id": lesson_id,
            "completed": True,
            "completed_items": [0, 1, 2, 3, 4, 5, 6, 7]  # More items completed
        }
        
        try:
            response = self.session.post(f"{API_URL}/progress", json=updated_progress)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    # Verify the update
                    response = self.session.get(f"{API_URL}/progress", params={"user_id": self.user_id})
                    if response.status_code == 200:
                        progress_list = response.json()
                        our_progress = next((p for p in progress_list if p.get("lesson_id") == lesson_id), None)
                        
                        if our_progress and len(our_progress.get("completed_items", [])) == 8:
                            self.log_test(
                                "Progress Tracking - Upsert Functionality", 
                                True, 
                                "Successfully updated existing progress record"
                            )
                        else:
                            self.log_test(
                                "Progress Tracking - Upsert Functionality", 
                                False, 
                                "Progress was not properly updated"
                            )
                else:
                    self.log_test(
                        "Progress Tracking - Upsert Functionality", 
                        False, 
                        "Upsert response indicates failure", 
                        result
                    )
            else:
                self.log_test(
                    "Progress Tracking - Upsert Functionality", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Progress Tracking - Upsert Functionality", False, f"Exception: {str(e)}")

    def test_6_favorites(self):
        """Test 6: Favorites - POST /api/favorites (toggle) and GET /api/favorites"""
        print("=== Test 6: Favorites ===")
        
        if not self.lesson_ids:
            self.log_test("Favorites", False, "No lesson IDs available for testing")
            return
            
        lesson_id = self.lesson_ids[0]
        
        # Test adding a favorite
        favorite_data = {
            "user_id": self.user_id,
            "lesson_id": lesson_id,
            "item_index": 0,
            "item_data": {
                "thai": "สวัสดี",
                "romanization": "sawatdee",
                "english": "Hello / Goodbye",
                "example": "สวัสดีครับ (male) / สวัสดีค่ะ (female)"
            }
        }
        
        try:
            response = self.session.post(f"{API_URL}/favorites", json=favorite_data)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and result.get("action") == "added":
                    self.log_test(
                        "Favorites - Add Favorite", 
                        True, 
                        f"Successfully added favorite. ID: {result.get('id', 'N/A')}"
                    )
                else:
                    self.log_test(
                        "Favorites - Add Favorite", 
                        False, 
                        f"Unexpected response: {result}"
                    )
            else:
                self.log_test(
                    "Favorites - Add Favorite", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Favorites - Add Favorite", False, f"Exception: {str(e)}")
        
        # Test retrieving favorites
        try:
            response = self.session.get(f"{API_URL}/favorites", params={"user_id": self.user_id})
            
            if response.status_code == 200:
                favorites = response.json()
                
                if isinstance(favorites, list) and len(favorites) > 0:
                    # Find our added favorite
                    our_favorite = next((f for f in favorites if f.get("lesson_id") == lesson_id and f.get("item_index") == 0), None)
                    
                    if our_favorite:
                        required_fields = ["user_id", "lesson_id", "item_index", "item_data"]
                        if all(field in our_favorite for field in required_fields):
                            self.log_test(
                                "Favorites - Retrieve Favorites", 
                                True, 
                                f"Successfully retrieved {len(favorites)} favorites"
                            )
                        else:
                            missing_fields = [field for field in required_fields if field not in our_favorite]
                            self.log_test(
                                "Favorites - Retrieve Favorites", 
                                False, 
                                f"Favorite missing required fields: {missing_fields}"
                            )
                    else:
                        self.log_test(
                            "Favorites - Retrieve Favorites", 
                            False, 
                            f"Added favorite not found. Total favorites: {len(favorites)}"
                        )
                else:
                    self.log_test(
                        "Favorites - Retrieve Favorites", 
                        False, 
                        f"Expected list with favorites, got: {type(favorites)} with length {len(favorites) if isinstance(favorites, list) else 'N/A'}"
                    )
            else:
                self.log_test(
                    "Favorites - Retrieve Favorites", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Favorites - Retrieve Favorites", False, f"Exception: {str(e)}")
        
        # Test removing favorite (toggle functionality)
        try:
            response = self.session.post(f"{API_URL}/favorites", json=favorite_data)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") and result.get("action") == "removed":
                    # Verify favorite was removed
                    response = self.session.get(f"{API_URL}/favorites", params={"user_id": self.user_id})
                    if response.status_code == 200:
                        favorites = response.json()
                        our_favorite = next((f for f in favorites if f.get("lesson_id") == lesson_id and f.get("item_index") == 0), None)
                        
                        if not our_favorite:
                            self.log_test(
                                "Favorites - Toggle Remove", 
                                True, 
                                "Successfully removed favorite via toggle"
                            )
                        else:
                            self.log_test(
                                "Favorites - Toggle Remove", 
                                False, 
                                "Favorite was not actually removed"
                            )
                else:
                    self.log_test(
                        "Favorites - Toggle Remove", 
                        False, 
                        f"Expected 'removed' action, got: {result}"
                    )
            else:
                self.log_test(
                    "Favorites - Toggle Remove", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_test("Favorites - Toggle Remove", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"🚀 Starting Thai Language Learning API Tests")
        print(f"📍 Backend URL: {API_URL}")
        print(f"👤 Test User ID: {self.user_id}")
        print("=" * 60)
        
        # Run tests in sequence as specified in the test plan
        self.test_1_data_initialization()
        self.test_2_get_all_lessons()
        self.test_3_get_lessons_by_category()
        self.test_4_get_lesson_by_id()
        self.test_5_progress_tracking()
        self.test_6_favorites()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}: {result['details']}")
        
        print("\n" + "=" * 60)
        return failed_tests == 0

if __name__ == "__main__":
    tester = ThaiLearningAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)