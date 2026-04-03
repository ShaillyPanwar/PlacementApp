import json
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os

# Default placement data (fallback when web scraping fails)
DEFAULT_PLACEMENT_DATA = [
    {
        "company_name": "TCS",
        "sector": "IT",
        "cgpa_requirement": 7.0,
        "eligible_branches": ["CSE", "IT", "ECE"],
        "backlogs_allowed": "As per policy",
        "ctc": "13.5 LPA",
        "stipend": "30000",
        "drive_date": "2024-12-15",
        "application_deadline": "2024-12-01",
        "selection_process": ["Online Test", "Technical Interview", "HR Round"],
        "internship_duration": "6 months",
        "internship_location": "India",
        "placement_stats": {
            "2023": {"total_offers": 45, "avg_ctc": "13.2 LPA"},
            "2022": {"total_offers": 38, "avg_ctc": "12.8 LPA"}
        },
        "source": "JIMS Rohini Official Website"
    },
    {
        "company_name": "Infosys",
        "sector": "IT",
        "cgpa_requirement": 6.5,
        "eligible_branches": ["CSE", "IT", "ECE", "Mechanical"],
        "backlogs_allowed": "As per policy",
        "ctc": "12.5 LPA",
        "stipend": "25000",
        "drive_date": "2024-12-20",
        "application_deadline": "2024-12-05",
        "selection_process": ["Written Test", "Technical Interview", "HR Round"],
        "internship_duration": "6 months",
        "internship_location": "India",
        "placement_stats": {
            "2023": {"total_offers": 52, "avg_ctc": "12.1 LPA"},
            "2022": {"total_offers": 48, "avg_ctc": "11.8 LPA"}
        },
        "source": "JIMS Rohini Official Website"
    },
    {
        "company_name": "Wipro",
        "sector": "IT",
        "cgpa_requirement": 6.0,
        "eligible_branches": ["CSE", "IT"],
        "backlogs_allowed": "As per policy",
        "ctc": "11.5 LPA",
        "stipend": "20000",
        "drive_date": "2024-12-25",
        "application_deadline": "2024-12-10",
        "selection_process": ["Online Assessment", "Technical Round", "HR Round"],
        "internship_duration": "6 months",
        "internship_location": "India",
        "placement_stats": {
            "2023": {"total_offers": 35, "avg_ctc": "11.2 LPA"},
            "2022": {"total_offers": 30, "avg_ctc": "10.9 LPA"}
        },
        "source": "JIMS Rohini Official Website"
    },
    {
        "company_name": "HCL Technologies",
        "sector": "IT",
        "cgpa_requirement": 6.2,
        "eligible_branches": ["CSE", "IT", "ECE"],
        "backlogs_allowed": "As per policy",
        "ctc": "11.0 LPA",
        "stipend": "18000",
        "drive_date": "2024-12-28",
        "application_deadline": "2024-12-12",
        "selection_process": ["Coding Test", "Technical Interview", "HR Round"],
        "internship_duration": "6 months",
        "internship_location": "India",
        "placement_stats": {
            "2023": {"total_offers": 28, "avg_ctc": "10.8 LPA"},
            "2022": {"total_offers": 25, "avg_ctc": "10.5 LPA"}
        },
        "source": "JIMS Rohini Official Website"
    },
    {
        "company_name": "Cognizant",
        "sector": "IT",
        "cgpa_requirement": 6.5,
        "eligible_branches": ["CSE", "IT"],
        "backlogs_allowed": "As per policy",
        "ctc": "12.0 LPA",
        "stipend": "22000",
        "drive_date": "2025-01-05",
        "application_deadline": "2024-12-20",
        "selection_process": ["Assessment Test", "Technical Interview", "HR Round"],
        "internship_duration": "6 months",
        "internship_location": "India",
        "placement_stats": {
            "2023": {"total_offers": 40, "avg_ctc": "11.9 LPA"},
            "2022": {"total_offers": 35, "avg_ctc": "11.5 LPA"}
        },
        "source": "JIMS Rohini Official Website"
    },
    {
        "company_name": "Accenture",
        "sector": "IT",
        "cgpa_requirement": 6.0,
        "eligible_branches": ["CSE", "IT", "ECE", "Mechanical"],
        "backlogs_allowed": "As per policy",
        "ctc": "10.5 LPA",
        "stipend": "15000",
        "drive_date": "2025-01-10",
        "application_deadline": "2024-12-25",
        "selection_process": ["Written Test", "Group Discussion", "Technical Interview", "HR Round"],
        "internship_duration": "6 months",
        "internship_location": "India",
        "placement_stats": {
            "2023": {"total_offers": 50, "avg_ctc": "10.2 LPA"},
            "2022": {"total_offers": 45, "avg_ctc": "9.9 LPA"}
        },
        "source": "JIMS Rohini Official Website"
    }
]

def prepare_documents(cleaned_data):
    """Convert cleaned data to text documents"""
    documents = []
    
    for record in cleaned_data:
        # Create readable text from structured data
        text = f"""
Company: {record.get('company_name', '')}
Sector: {record.get('sector', '')}

Eligibility:
- CGPA Required: {record.get('cgpa_requirement', 'Not specified')}
- Eligible Branches: {', '.join(record.get('eligible_branches', []))}
- Backlogs: {record.get('backlogs_allowed', 'Not specified')}

Compensation:
- CTC: {record.get('ctc', '')}
- Stipend: {record.get('stipend', '')}

Drive Timeline:
- Date: {record.get('drive_date', 'Not announced')}
- Deadline: {record.get('application_deadline', 'Not specified')}

Selection Process:
{', '.join(record.get('selection_process', []))}

Internship:
- Duration: {record.get('internship_duration', '')}
- Location: {record.get('internship_location', 'Not specified')}

Statistics: {json.dumps(record.get('placement_stats', {}), indent=2)}
        """
        documents.append(text.strip())
    
    return documents

def load_data_with_fallback():
    """
    Load cleaned data. If not available, use default data.
    Returns tuple: (data, source_type)
    """
    cleaned_file = Path("data/cleaned/placement_data_cleaned.json")
    
    if cleaned_file.exists():
        print("✓ Loading cleaned data from file...")
        with open(cleaned_file, 'r') as f:
            data = json.load(f)
        return data, "cleaned_file"
    
    raw_file = Path("data/raw/placement_data.json")
    if raw_file.exists():
        print("✓ Loading raw data from file...")
        with open(raw_file, 'r') as f:
            data = json.load(f)
        return data, "raw_file"
    
    print("⚠️  No data files found. Using DEFAULT DATA...")
    return DEFAULT_PLACEMENT_DATA, "default"

def create_knowledge_base(force_default=False):
    """
    Phase 3: Knowledge Base Creation
    
    Sub-step 1: Chunking - Break documents into 300-500 word pieces
    Sub-step 2: Embedding - Convert to vectors using sentence-transformers
    Sub-step 3: Storage - Store in ChromaDB for fast searching
    
    Args:
        force_default: If True, ignore existing files and use default data
    """
    
    print("\n" + "="*60)
    print("📚 PHASE 3: KNOWLEDGE BASE CREATION")
    print("="*60)
    
    # Load data with fallback
    if force_default:
        print("🔧 Force using default data...")
        data, source = DEFAULT_PLACEMENT_DATA, "default"
    else:
        data, source = load_data_with_fallback()
    
    print(f"📊 Loaded {len(data)} records from: {source}")
    
    # SUB-STEP 1: Chunking
    print("\n🔀 Sub-step 1: Chunking documents...")
    documents = prepare_documents(data)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = []
    for doc in documents:
        doc_chunks = splitter.split_text(doc)
        chunks.extend(doc_chunks)
    
    print(f"✓ Created {len(chunks)} text chunks")
    
    # SUB-STEP 2: Embedding
    print("\n🧠 Sub-step 2: Creating embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("✓ Embeddings model loaded")
    
    # SUB-STEP 3: Storage in ChromaDB
    print("\n💾 Sub-step 3: Storing in ChromaDB...")
    
    db_path = Path("knowledge_base/chroma_db")
    
    # Remove old database if it exists (fresh start)
    if db_path.exists():
        import shutil
        shutil.rmtree(db_path)
        print("🗑️  Cleaned old database")
    
    db_path.mkdir(parents=True, exist_ok=True)
    
    # Create vector store
    vector_store = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=str(db_path)
    )
    vector_store.persist()
    
    print(f"✓ Knowledge base created at: {db_path}")
    print(f"✓ Total vectors stored: {len(chunks)}")
    print(f"✓ Data source: {source}")
    
    return vector_store

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build knowledge base')
    parser.add_argument('--default', action='store_true', 
                       help='Force use default data even if files exist')
    args = parser.parse_args()
    
    create_knowledge_base(force_default=args.default)
    
    print("\n" + "="*60)
    print("✅ Knowledge Base Creation Complete!")
    print("="*60)
    print("\n💡 Next Steps:")
    print("   1. Run: python app.py")
    print("   2. Open: http://localhost:5000 in your browser")
    print("   3. Start testing queries!")

if __name__ == "__main__":
    main()
