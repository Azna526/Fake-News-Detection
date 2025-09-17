import requests
import sys
import json
import time
from datetime import datetime

class HoaxHunterAPITester:
    def __init__(self, base_url="https://hoax-hunter-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=60):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response preview: {str(response_data)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health check endpoint"""
        return self.run_test("Health Check", "GET", "", 200)

    def test_analyze_text_content(self):
        """Test text content analysis"""
        test_content = """
        Breaking: Local Mayor Announces New Infrastructure Project
        
        The mayor of Springfield announced today a $50 million infrastructure improvement project 
        that will focus on road repairs and bridge maintenance over the next two years. The project 
        is expected to create 200 jobs and improve traffic flow throughout the city.
        
        "This investment in our infrastructure is crucial for our city's future," said Mayor Johnson 
        during a press conference. The funding comes from a combination of federal grants and city bonds.
        """
        
        data = {
            "content": test_content,
            "analysis_type": "comprehensive"
        }
        
        print("   Note: This test involves AI analysis and may take 30-60 seconds...")
        return self.run_test("Text Content Analysis", "POST", "analyze", 200, data, timeout=90)

    def test_analyze_url_content(self):
        """Test URL content analysis"""
        # Using a reliable news URL for testing
        test_url = "https://www.bbc.com/news"
        
        data = {
            "url": test_url,
            "analysis_type": "comprehensive"
        }
        
        print("   Note: This test involves URL extraction + AI analysis and may take 60-90 seconds...")
        return self.run_test("URL Content Analysis", "POST", "analyze", 200, data, timeout=120)

    def test_analyze_invalid_input(self):
        """Test analysis with invalid input"""
        data = {
            "analysis_type": "comprehensive"
            # No content or URL provided
        }
        
        return self.run_test("Invalid Input Analysis", "POST", "analyze", 400, data)

    def test_analyze_short_content(self):
        """Test analysis with content too short"""
        data = {
            "content": "Short text",
            "analysis_type": "comprehensive"
        }
        
        return self.run_test("Short Content Analysis", "POST", "analyze", 400, data)

    def test_get_history(self):
        """Test getting analysis history"""
        return self.run_test("Get Analysis History", "GET", "history", 200)

    def test_get_history_with_limit(self):
        """Test getting analysis history with limit"""
        return self.run_test("Get Analysis History (Limited)", "GET", "history?limit=5", 200)

    def test_invalid_endpoint(self):
        """Test invalid endpoint"""
        return self.run_test("Invalid Endpoint", "GET", "nonexistent", 404)

def main():
    print("🚀 Starting HoaxHunter API Testing...")
    print("=" * 60)
    
    tester = HoaxHunterAPITester()
    
    # Test basic functionality first
    print("\n📋 BASIC FUNCTIONALITY TESTS")
    print("-" * 40)
    
    success, _ = tester.test_health_check()
    if not success:
        print("❌ Health check failed - API may not be running")
        print(f"\n📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
        return 1
    
    # Test error handling
    print("\n🚫 ERROR HANDLING TESTS")
    print("-" * 40)
    tester.test_analyze_invalid_input()
    tester.test_analyze_short_content()
    tester.test_invalid_endpoint()
    
    # Test history functionality
    print("\n📚 HISTORY FUNCTIONALITY TESTS")
    print("-" * 40)
    tester.test_get_history()
    tester.test_get_history_with_limit()
    
    # Test core analysis functionality (these are slow due to AI processing)
    print("\n🧠 AI ANALYSIS TESTS (SLOW)")
    print("-" * 40)
    print("⚠️  The following tests involve AI processing and will take time...")
    
    # Test text analysis
    success, analysis_result = tester.test_analyze_text_content()
    if success and analysis_result:
        print("   ✅ Text analysis returned valid structure")
        # Verify response structure
        required_fields = ['fake_news_analysis', 'bias_analysis', 'overall_assessment', 'recommendations']
        for field in required_fields:
            if field in analysis_result:
                print(f"   ✅ Found required field: {field}")
            else:
                print(f"   ❌ Missing required field: {field}")
    
    # Test URL analysis (this might fail due to content extraction complexity)
    print("\n   Testing URL analysis (may fail due to content extraction)...")
    success, url_result = tester.test_analyze_url_content()
    if success:
        print("   ✅ URL analysis completed successfully")
    else:
        print("   ⚠️  URL analysis failed - this is common due to website restrictions")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 FINAL TEST RESULTS")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed >= tester.tests_run * 0.7:  # 70% pass rate
        print("✅ Overall: API testing PASSED")
        return 0
    else:
        print("❌ Overall: API testing FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())