from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize LLM Chat
llm_key = os.environ.get('EMERGENT_LLM_KEY')
if not llm_key:
    raise ValueError("EMERGENT_LLM_KEY not found in environment variables")

# Define Models
class NewsAnalysisRequest(BaseModel):
    content: Optional[str] = None
    url: Optional[str] = None
    analysis_type: str = "comprehensive"  # comprehensive, basic

class BiasAnalysis(BaseModel):
    bias_score: float  # 0-10 scale, 0 being neutral, 10 being extremely biased
    bias_type: str  # political, commercial, emotional, etc.
    bias_indicators: List[str]
    explanation: str

class SourceCredibility(BaseModel):
    credibility_score: float  # 0-10 scale
    credibility_factors: List[str]
    reputation_indicators: List[str]
    concerns: List[str]

class FakeNewsAnalysis(BaseModel):
    is_fake: bool
    confidence_score: float  # 0-100 scale
    classification: str  # "Real News", "Fake News", "Misleading", "Satirical", "Opinion"
    reasoning: List[str]
    evidence: List[str]
    red_flags: List[str]

class NewsAnalysisResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    source_url: Optional[str]
    fake_news_analysis: FakeNewsAnalysis
    bias_analysis: BiasAnalysis
    source_credibility: Optional[SourceCredibility]
    overall_assessment: str
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnalysisHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    analysis: NewsAnalysisResponse
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

async def extract_content_from_url(url: str) -> tuple[str, str]:
    """Extract content from URL and return (content, title)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise HTTPException(status_code=400, detail=f"Failed to fetch URL: HTTP {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "No title found"
                
                # Extract main content
                content_selectors = [
                    'article', '.article-content', '.post-content', 
                    '.entry-content', 'main', '.main-content',
                    '.story-body', '.article-body'
                ]
                
                content = ""
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = ' '.join([elem.get_text() for elem in elements])
                        break
                
                if not content:
                    # Fallback to paragraphs
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text() for p in paragraphs])
                
                # Clean up text
                content = re.sub(r'\s+', ' ', content).strip()
                
                if len(content) < 100:
                    raise HTTPException(status_code=400, detail="Insufficient content extracted from URL")
                
                return content, title_text
                
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting content: {str(e)}")

async def analyze_with_llm(content: str, url: Optional[str] = None) -> NewsAnalysisResponse:
    """Analyze content using OpenAI GPT-4o for comprehensive fake news detection"""
    
    system_message = """You are an expert fact-checker and media analyst with extensive experience in identifying fake news, misinformation, bias, and assessing source credibility. Your task is to provide comprehensive analysis of news content.

For each analysis, evaluate:
1. FAKE NEWS DETECTION: Determine if content is real, fake, misleading, satirical, or opinion-based
2. BIAS ANALYSIS: Identify political, commercial, emotional, or other biases
3. SOURCE CREDIBILITY: Assess the reliability and reputation of the source (if URL provided)
4. EVIDENCE & REASONING: Provide specific examples and explanations

Return your analysis in the following JSON format:
{
  "fake_news_analysis": {
    "is_fake": boolean,
    "confidence_score": float (0-100),
    "classification": string ("Real News", "Fake News", "Misleading", "Satirical", "Opinion"),
    "reasoning": [list of specific reasons],
    "evidence": [list of evidence supporting the classification],
    "red_flags": [list of warning signs or suspicious elements]
  },
  "bias_analysis": {
    "bias_score": float (0-10, where 0 is neutral),
    "bias_type": string (primary type of bias detected),
    "bias_indicators": [list of specific bias indicators],
    "explanation": string (detailed explanation of bias detected)
  },
  "source_credibility": {
    "credibility_score": float (0-10),
    "credibility_factors": [list of positive credibility factors],
    "reputation_indicators": [list of reputation indicators],
    "concerns": [list of credibility concerns]
  },
  "overall_assessment": string (summary of overall findings),
  "recommendations": [list of recommendations for readers]
}

Be thorough but concise. Provide specific examples from the content to support your analysis."""

    try:
        # Initialize chat session
        chat = LlmChat(
            api_key=llm_key,
            session_id=str(uuid.uuid4()),
            system_message=system_message
        ).with_model("openai", "gpt-4o")
        
        # Prepare analysis prompt
        analysis_prompt = f"""Please analyze the following content for fake news, bias, and credibility:

CONTENT TO ANALYZE:
{content[:8000]}  # Limit content to avoid token limits

SOURCE URL: {url if url else "Not provided"}

Provide your analysis in the specified JSON format."""

        user_message = UserMessage(text=analysis_prompt)
        response = await chat.send_message(user_message)
        
        # Parse the LLM response
        import json
        try:
            analysis_data = json.loads(response)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                raise HTTPException(status_code=500, detail="Failed to parse analysis response")
        
        # Create response object
        fake_news_analysis = FakeNewsAnalysis(**analysis_data["fake_news_analysis"])
        bias_analysis = BiasAnalysis(**analysis_data["bias_analysis"])
        source_credibility = SourceCredibility(**analysis_data["source_credibility"]) if "source_credibility" in analysis_data else None
        
        analysis_response = NewsAnalysisResponse(
            content=content[:2000] + ("..." if len(content) > 2000 else ""),  # Truncate for storage
            source_url=url,
            fake_news_analysis=fake_news_analysis,
            bias_analysis=bias_analysis,
            source_credibility=source_credibility,
            overall_assessment=analysis_data["overall_assessment"],
            recommendations=analysis_data["recommendations"]
        )
        
        return analysis_response
        
    except Exception as e:
        logging.error(f"LLM analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# API Endpoints
@api_router.get("/")
async def root():
    return {"message": "Fake News Detection API is running"}

@api_router.post("/analyze", response_model=NewsAnalysisResponse)
async def analyze_news(request: NewsAnalysisRequest):
    """Analyze news content for fake news, bias, and credibility"""
    
    if not request.content and not request.url:
        raise HTTPException(status_code=400, detail="Either content or URL must be provided")
    
    content = request.content
    url = request.url
    
    # Extract content from URL if provided
    if request.url:
        try:
            extracted_content, title = await extract_content_from_url(request.url)
            content = f"{title}\n\n{extracted_content}"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract content from URL: {str(e)}")
    
    if not content or len(content.strip()) < 50:
        raise HTTPException(status_code=400, detail="Content is too short for meaningful analysis")
    
    # Perform analysis
    analysis = await analyze_with_llm(content, url)
    
    # Store in database
    try:
        history_entry = AnalysisHistory(analysis=analysis)
        analysis_dict = history_entry.dict()
        # Convert datetime to ISO string for MongoDB
        analysis_dict['timestamp'] = analysis_dict['timestamp'].isoformat()
        analysis_dict['analysis']['timestamp'] = analysis_dict['analysis']['timestamp'].isoformat()
        
        await db.analysis_history.insert_one(analysis_dict)
    except Exception as e:
        logging.warning(f"Failed to store analysis in database: {str(e)}")
    
    return analysis

@api_router.get("/history", response_model=List[AnalysisHistory])
async def get_analysis_history(limit: int = 20):
    """Get recent analysis history"""
    try:
        history = await db.analysis_history.find().sort("timestamp", -1).limit(limit).to_list(length=limit)
        
        for item in history:
            # Convert ISO strings back to datetime objects
            if isinstance(item.get('timestamp'), str):
                item['timestamp'] = datetime.fromisoformat(item['timestamp'])
            if isinstance(item.get('analysis', {}).get('timestamp'), str):
                item['analysis']['timestamp'] = datetime.fromisoformat(item['analysis']['timestamp'])
        
        return [AnalysisHistory(**item) for item in history]
    except Exception as e:
        logging.error(f"Failed to fetch history: {str(e)}")
        return []

@api_router.delete("/history/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete a specific analysis from history"""
    try:
        result = await db.analysis_history.delete_one({"id": analysis_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return {"message": "Analysis deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()