import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_qdrant import QdrantVectorStore
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


import os
from typing import List
import logging

logger = logging.getLogger(__name__)

class SimpleRAGEngine:
    def __init__(self, qdrant_url: str, redis_url: str, document_path: str):
        """
        Initialize a simple RAG engine for the chatbot service
        
        Args:
            qdrant_url: Qdrant connection URL (e.g., "http://localhost:6333")
            redis_url: Redis URL for chat history
            document_path: Path to your project documentation file
        """
        self.qdrant_url = qdrant_url
        self.redis_url = redis_url
        self.document_path = document_path
        
        # For now, use a simple fallback implementation
        # TODO: Implement full RAG with proper embeddings when AI packages are stable
        self.knowledge_base = self._load_simple_knowledge_base()
    
    def _load_simple_knowledge_base(self) -> dict:
        """Load a simple knowledge base from the documentation file"""
        knowledge = {}
        
        try:
            if os.path.exists(self.document_path):
                with open(self.document_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    knowledge['project_info'] = content[:2000]  # First 2000 chars
            else:
                logger.warning(f"Documentation file not found: {self.document_path}")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
        
        # Add some basic FAQ responses
        knowledge.update({
            'blockchain': 'This is a blockchain-powered Learning Management System that uses tokens for course access and NFT certificates for completion.',
            'courses': 'You can browse available courses, enroll in them, and track your progress. Some courses require tokens for access.',
            'tokens': 'Tokens are used to access premium courses and features. You can earn tokens by completing lessons and quizzes.',
            'certificates': 'Upon course completion, you receive an NFT certificate stored on the blockchain as proof of your achievement.',
            'wallet': 'Connect your MetaMask wallet to access blockchain features like token payments and certificate minting.',
        })
        
        return knowledge
    
    def chat(self, session_id: str, user_message: str) -> str:
        """
        Simple chat implementation using keyword matching
        
        Args:
            session_id: Unique session identifier
            user_message: User's question
            
        Returns:
            Assistant's response
        """
        try:
            user_message_lower = user_message.lower()
            
            # Simple keyword matching
            if any(word in user_message_lower for word in ['blockchain', 'chain', 'crypto']):
                return self.knowledge_base.get('blockchain', 'This platform uses blockchain technology for secure course management.')
            
            elif any(word in user_message_lower for word in ['course', 'learn', 'lesson']):
                return self.knowledge_base.get('courses', 'You can browse and enroll in various courses available on the platform.')
            
            elif any(word in user_message_lower for word in ['token', 'payment', 'pay']):
                return self.knowledge_base.get('tokens', 'Tokens are used for accessing premium courses and earning rewards.')
            
            elif any(word in user_message_lower for word in ['certificate', 'nft', 'completion']):
                return self.knowledge_base.get('certificates', 'You receive NFT certificates upon successful course completion.')
            
            elif any(word in user_message_lower for word in ['wallet', 'metamask', 'connect']):
                return self.knowledge_base.get('wallet', 'Connect your MetaMask wallet to access blockchain features.')
            
            elif any(word in user_message_lower for word in ['help', 'support']):
                return """I can help you with:
• Information about courses and enrollment
• Blockchain features and token usage
• NFT certificates and achievements
• Wallet connection and setup
• General platform navigation

What would you like to know more about?"""
            
            else:
                return """I'm here to help with questions about the Blockchain AI LMS platform. You can ask me about:
• Courses and enrollment
• Blockchain features
• Tokens and payments
• NFT certificates
• Wallet connection

What would you like to know?"""
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later."

    def _ensure_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        collections = [c.name for c in self.qdrant_client.get_collections().collections]
        if self.collection_name not in collections:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts using google-genai embeddings"""
        result = self.client.models.embed_content(
            model=self.embedding_model,
            input=texts
        )
        # The API returns a list of embedding dicts
        return [e.values for e in result.embeddings]

    def _load_document(self, document_path: str):
        """Load and index the documentation file"""
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_text(content)
        documents = [Document(page_content=chunk) for chunk in chunks]
        self.vector_store.add_documents(documents)

    def _setup_chain(self):
        """Build a simple retrieval + chat generation pipeline"""
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant for a blockchain-powered LMS.
            Use the retrieved context below to answer accurately and concisely.
            If you’re unsure, say so.

            Context: {context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])

    def _generate_response(self, prompt_text: str) -> str:
        """Generate text with Gemini via google-genai"""
        response = self.client.models.generate_content(
            model=self.chat_model,
            contents=prompt_text
        )
        return response.text

    def chat(self, session_id: str, user_message: str) -> str:
        """Chat endpoint with RAG + Redis history"""
        message_history = RedisChatMessageHistory(
            session_id=session_id,
            url=self.redis_url
        )

        # Retrieve relevant context
        docs = self.retriever.invoke({"query": user_message})
        context = "\n\n".join(doc.page_content for doc in docs)

        # Combine into prompt
        prompt_text = self.prompt.format(
            context=context,
            chat_history=message_history.messages,
            question=user_message
        )

        # Get response from Gemini
        response_text = self._generate_response(prompt_text)

        # Save to Redis history
        message_history.add_user_message(user_message)
        message_history.add_ai_message(response_text)

        return response_text
