"""
VaultZero RAG System
Loads 23 ZT assessments into Chroma vector database for intelligent search
"""

import json
import os
from typing import List, Dict
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class VaultZeroRAG:
    def __init__(self, data_path: str, persist_directory: str = "./data/chroma_db"):
        """
        Initialize VaultZero RAG system
        
        Args:
            data_path: Path to zt_synthetic_dataset_complete.json
            persist_directory: Where to save the vector database
        """
        self.data_path = data_path
        self.persist_directory = persist_directory
        
        # Initialize embeddings (FREE - runs locally)
        print("🔄 Loading embedding model (this may take a minute first time)...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        self.vectorstore = None
        self.assessments = []
        
    def load_assessments(self) -> List[Dict]:
        """Load all 23 assessments from JSON file"""
        print(f"📂 Loading assessments from: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # The complete dataset should be a list of assessments
        if isinstance(data, dict):
            self.assessments = data.get('assessments', data.get('data', [data]))
        else:
            self.assessments = data
            
        print(f"✅ Loaded {len(self.assessments)} assessments")
        return self.assessments
    
    def prepare_documents(self) -> List[Document]:
        """Convert assessments to LangChain Documents for vector DB"""
        print("🔄 Preparing documents for vector database...")
        
        documents = []
        
        for idx, assessment in enumerate(self.assessments):
            system_id = assessment.get('system_id', f'SYSTEM-{idx}')
            system_type = assessment.get('system_type', 'Unknown')
            overall_maturity = assessment.get('overall_maturity_level', 'Unknown')
            
            text_parts = [
                f"System ID: {system_id}",
                f"System Type: {system_type}",
                f"Overall Maturity: {overall_maturity}",
                f"Description: {assessment.get('system_description', '')}",
            ]
            
            pillars = assessment.get('pillars', {})
            for pillar_name, pillar_data in pillars.items():
                if isinstance(pillar_data, dict):
                    maturity = pillar_data.get('maturity_level', 'Unknown')
                    score = pillar_data.get('score', 'N/A')
                    text_parts.append(f"{pillar_name} Pillar: {maturity} (Score: {score})")
                    
                    qa_pairs = pillar_data.get('detailed_assessment', [])
                    for qa in qa_pairs:
                        if isinstance(qa, dict):
                            q = qa.get('question', '')
                            a = qa.get('answer', '')
                            text_parts.append(f"Q: {q}\nA: {a}")
            
            full_text = "\n".join(text_parts)
            
            metadata = {
                'system_id': system_id,
                'system_type': system_type,
                'overall_maturity': overall_maturity,
                'assessment_index': idx
            }
            
            doc = Document(page_content=full_text, metadata=metadata)
            documents.append(doc)
        
        print(f"✅ Prepared {len(documents)} documents")
        return documents
    
    def create_vectorstore(self, documents: List[Document]):
        """Create and persist Chroma vector database"""
        print("🔄 Creating vector database (this may take 1-2 minutes)...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        print(f"📄 Split into {len(splits)} chunks")
        
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        self.vectorstore.persist()
        print(f"✅ Vector database created and saved to {self.persist_directory}")
        
    def load_existing_vectorstore(self):
        """Load previously created vector database"""
        print(f"🔄 Loading existing vector database from {self.persist_directory}...")
        
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        
        print("✅ Vector database loaded")
        
    def search_similar_systems(self, query: str, k: int = 3) -> List[Dict]:
        """Search for similar systems"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized. Call create_vectorstore() first.")
        
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'similarity_score': score,
                'system_id': doc.metadata.get('system_id'),
                'system_type': doc.metadata.get('system_type'),
                'maturity': doc.metadata.get('overall_maturity')
            })
        
        return formatted_results
    
    def initialize(self, force_rebuild: bool = False):
        """Complete initialization workflow"""
        self.load_assessments()
        
        db_exists = os.path.exists(os.path.join(self.persist_directory, 'chroma.sqlite3'))
        
        if db_exists and not force_rebuild:
            print("📦 Existing vector database found")
            self.load_existing_vectorstore()
        else:
            print("🏗️ Building new vector database...")
            documents = self.prepare_documents()
            self.create_vectorstore(documents)
        
        print("✅ VaultZero RAG system ready!")