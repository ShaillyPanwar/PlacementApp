import json
from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os
from dotenv import load_dotenv
import requests
from urllib.parse import quote
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API (only for file uploads)
try:
    from google.genai import Client
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        client = Client(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        logger.info("✓ Gemini API available (for file uploads only)")
    else:
        client = None
        GEMINI_AVAILABLE = False
        logger.warning("⚠️ Gemini API key not found")
except ImportError:
    client = None
    GEMINI_AVAILABLE = False
    logger.warning("⚠️ google-generativeai not installed")

class PlacementChatbot:
    def __init__(self):
        """Initialize the RAG chatbot"""
        logger.info("🚀 Initializing Placement Chatbot...")
        
        # Load embeddings
        logger.info("Loading embeddings model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Load vector store
        db_path = Path("knowledge_base/chroma_db")
        logger.info("Loading vector store...")
        self.vector_store = Chroma(
            persist_directory=str(db_path),
            embedding_function=self.embeddings
        )
        
        # Create retriever
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 3}
        )
        
        self.client = client
        logger.info("✓ Chatbot initialized successfully!")
    
    def query_knowledge_base(self, question):
        """Query local knowledge base"""
        try:
            retrieved_docs = self.retriever.invoke(question)
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            return context, retrieved_docs
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return "", []
    
    def search_wikipedia(self, query):
        """Search Wikipedia for information"""
        try:
            logger.info(f"📚 Searching Wikipedia for: {query}")
            
            # Wikipedia API endpoint
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'srsearch': query,
                'srlimit': 1
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if 'query' in data and 'search' in data['query'] and len(data['query']['search']) > 0:
                search_result = data['query']['search'][0]
                page_title = search_result['title']
                
                # Get page content
                page_params = {
                    'action': 'query',
                    'format': 'json',
                    'titles': page_title,
                    'prop': 'extracts',
                    'explaintext': True,
                    'exintro': True
                }
                
                page_response = requests.get(url, params=page_params, timeout=5)
                page_data = page_response.json()
                
                if 'query' in page_data and 'pages' in page_data['query']:
                    pages = page_data['query']['pages']
                    for page_id, page_info in pages.items():
                        if 'extract' in page_info:
                            extract = page_info['extract'][:800]  # First 800 chars
                            logger.info(f"✓ Found Wikipedia result")
                            return f"📖 **From Wikipedia:**\n\n{extract}"
            
            logger.info("No Wikipedia results found")
            return None
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return None
    
    def search_web(self, query):
        """Search using DuckDuckGo (free alternative to Google)"""
        try:
            logger.info(f"🔍 Searching web for: {query}")
            
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if 'Abstract' in data and data['Abstract']:
                result = f"🔍 **From Web Search:**\n\n{data['Abstract']}"
                if 'AbstractSource' in data:
                    result += f"\n\n_Source: {data['AbstractSource']}_"
                logger.info("✓ Found web search result")
                return result
            
            logger.info("No web search results found")
            return None
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return None
    
    def is_placement_related(self, question):
        """Check if question is about placements"""
        placement_keywords = [
            'placement', 'company', 'cgpa', 'ctc', 'salary', 'intern',
            'interview', 'tcs', 'infosys', 'wipro', 'hcl', 'cognizant', 'accenture',
            'drive', 'recruitment', 'eligibility', 'branch', 'selection',
            'round', 'technical', 'hr', 'compensation', 'stipend', 'offer',
            'jims', 'college', 'job', 'hiring', 'requirements', 'criteria',
            'deadline', 'date', 'application', 'backlogs', 'gpa', 'score'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in placement_keywords)
    
    def query_gemini_for_file(self, text, question=""):
        """Use Gemini API ONLY for file analysis"""
        if not self.client or not GEMINI_AVAILABLE:
            return "Gemini API not available for file analysis"
        
        prompt = f"""You are an expert interview preparation assistant. Analyze the provided content and help the student prepare for interviews.

Content:
{text[:5000]}

User's question: {question if question else "Analyze this and help me prepare"}

Please provide:
1. **Summary**: Key points from the content
2. **Key Concepts**: Important topics to understand
3. **Interview Relevance**: How this helps with interviews
4. **Practice Questions**: 3-5 questions based on this content
5. **Study Tips**: How to master these concepts

Be practical and focused on interview preparation."""
        
        try:
            logger.info("📤 Sending file to Gemini for analysis...")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            logger.info("✓ Gemini file analysis completed")
            return response.text
        except Exception as e:
            logger.error(f"Gemini file analysis error: {e}")
            return f"File analysis error: {str(e)}"
    
    def query(self, question):
        """Query the chatbot"""
        logger.info(f"📝 Query: {question}")
        
        # Step 1: Check if question is placement-related
        if self.is_placement_related(question):
            logger.info("✓ This is a placement-related question")
            # PLACEMENT QUESTION - Search database only
            context, docs = self.query_knowledge_base(question)
            
            if len(context.strip()) > 100:  # Found good context
                logger.info("✓ Found relevant placement info in database")
                return {
                    "question": question,
                    "answer": context,
                    "source": "Placement Database",
                    "is_placement_question": True
                }
            else:
                # No context found for placement question
                logger.info("No placement info found in database")
                answer = f"ℹ️ I don't have specific information about this in my placement database.\n\nI can help with:\n✓ Company eligibility (CGPA, branches)\n✓ CTC and stipend details\n✓ Selection process\n✓ Interview rounds\n\nPlease try asking about specific companies like TCS, Infosys, Wipro, etc."
                return {
                    "question": question,
                    "answer": answer,
                    "source": "Placement Database",
                    "is_placement_question": True
                }
        
        else:
            # NON-PLACEMENT QUESTION - Search web only (NO Gemini)
            logger.info("✓ This is a general question - searching web")
            
            # Try Wikipedia first
            web_answer = self.search_wikipedia(question)
            
            # If Wikipedia fails, try DuckDuckGo
            if not web_answer:
                web_answer = self.search_web(question)
            
            # If still no answer, return helpful message
            if not web_answer:
                logger.info("No web results found")
                web_answer = "❌ Sorry, I couldn't find information about this online.\n\nTry:\n• Being more specific\n• Using simpler keywords\n• Asking about placements instead (I have a dedicated database for that!)"
                source = "Web Search (No Results)"
            else:
                logger.info("✓ Found web answer")
                source = "Wikipedia/Web Search"
            
            return {
                "question": question,
                "answer": web_answer,
                "source": source,
                "is_placement_question": False
            }

def main():
    chatbot = PlacementChatbot()
    
    test_queries = [
        "What is TCS CGPA requirement?",
        "What is DSA?",
        "Tell me about machine learning",
        "How many rounds in Infosys interview?",
    ]
    
    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        result = chatbot.query(q)
        print(f"A: {result['answer'][:300]}...")
        print(f"Source: {result['source']}")

if __name__ == "__main__":
    main()