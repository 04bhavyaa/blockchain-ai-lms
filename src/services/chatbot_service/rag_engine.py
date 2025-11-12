import os
import logging
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

class SimpleRAGEngine:
    def __init__(self, qdrant_url: str, redis_url: str, document_path: str):
        """
        Initialize RAG engine with Qdrant and Google Gemini
        
        Args:
            qdrant_url: URL of the Qdrant vector database server
            redis_url: Redis URL for chat history
            document_path: Path to project documentation file
        """
        self.qdrant_url = qdrant_url
        self.redis_url = redis_url
        self.document_path = document_path
        
        try:
            # Initialize Google API key
            self.google_api_key = os.getenv("GOOGLE_API_KEY")
            if not self.google_api_key:
                logger.error("GOOGLE_API_KEY not found in environment variables")
                raise ValueError("GOOGLE_API_KEY is required")
            
            # Initialize embeddings and LLM
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=self.google_api_key
            )
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.7,
                google_api_key=self.google_api_key
            )
            
            # Setup vectorstore with Qdrant
            self._setup_vectorstore()
            
            # Setup RAG chain
            self._setup_chain()
            
            # Successfully initialized - no fallback needed
            self.use_fallback = False
            logger.info("RAG Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Engine: {e}", exc_info=True)
            # Fallback to simple responses
            self.use_fallback = True
            self._setup_fallback_responses()
    
    def _setup_vectorstore(self):
        """Setup Qdrant vectorstore with document loading"""
        try:
            # Check if we have embedding quota
            try:
                test_embed = self.embeddings.embed_query("test")
                has_embedding_quota = True
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    logger.warning("Embedding quota exceeded, will use LLM without RAG")
                    has_embedding_quota = False
                    self.use_simple_llm = True
                    return
                else:
                    raise
            
            if os.path.exists(self.document_path):
                with open(self.document_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split document into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000, 
                    chunk_overlap=200
                )
                
                chunks = text_splitter.split_text(content)
                documents = [Document(page_content=chunk) for chunk in chunks]
                
                collection_name = "rag_documents"
                
                # Create or connect to Qdrant collection
                self.vectorstore = Qdrant.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    collection_name=collection_name,
                    url=self.qdrant_url,
                    prefer_grpc=True  # optional, if grpc supported/preferred
                )
                
                self.retriever = self.vectorstore.as_retriever()
                logger.info(f"Qdrant vectorstore created with {len(documents)} documents")
                
            else:
                logger.warning(f"Document path not found: {self.document_path}")
                
                # Initialize empty Qdrant collection connection
                collection_name = "rag_documents"
                self.vectorstore = Qdrant(
                    embedding_function=self.embeddings,
                    collection_name=collection_name,
                    url=self.qdrant_url,
                    prefer_grpc=True
                )
                self.retriever = self.vectorstore.as_retriever()
                
        except Exception as e:
            logger.error(f"Error setting up vectorstore: {e}")
            raise
    
    def _setup_chain(self):
        """Setup RAG chain with conversation history"""
        # If using simple LLM without RAG
        if getattr(self, 'use_simple_llm', False):
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", 
                 "You are a helpful AI assistant for the Blockchain AI LMS platform. "
                 "Answer questions about blockchain-based learning, course enrollment, "
                 "token payments, NFT certificates, and wallet integration. "
                 "Be helpful, concise, and professional."),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ])
            
            self.simple_chain = (
                self.prompt
                | self.llm
                | StrOutputParser()
            )
            
            self.conversational_chain = RunnableWithMessageHistory(
                self.simple_chain,
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            return
        
        # Original RAG chain with retriever
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are a helpful AI assistant for the Blockchain AI LMS platform. "
             "Use the following context to answer the user's question accurately and concisely. "
             "If you don't know the answer, say you don't know. "
             "If the question is not related to the platform, politely decline to answer.\n\n"
             "Context: {context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        
        def format_docs(docs: Optional[List[Document]]):
            if not docs:
                return "No relevant context found."
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.rag_chain = (
            RunnablePassthrough.assign(
                context=(lambda x: x["input"]) | self.retriever | format_docs
            )
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        self.conversational_rag_chain = RunnableWithMessageHistory(
            self.rag_chain,
            self._get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
    
    def _get_session_history(self, session_id: str) -> RedisChatMessageHistory:
        """Get Redis chat history for session"""
        return RedisChatMessageHistory(
            session_id=session_id, 
            url=self.redis_url
        )
    
    def _setup_fallback_responses(self):
        """Setup fallback responses when RAG is not available"""
        self.fallback_responses = {
            'blockchain': 'This is a blockchain-powered Learning Management System that uses tokens for course access and NFT certificates for completion.',
            'courses': 'You can browse available courses, enroll in them, and track your progress. Some courses require tokens for access.',
            'tokens': 'Tokens are used to access premium courses and features. You can earn tokens by completing lessons and quizzes.',
            'certificates': 'Upon course completion, you receive an NFT certificate stored on the blockchain as proof of your achievement.',
            'wallet': 'Connect your MetaMask wallet to access blockchain features like token payments and certificate minting.',
        }
    
    def chat(self, session_id: str, user_message: str) -> str:
        """Chat with the RAG engine
        
        Args:
            session_id: Unique session identifier
            user_message: User's question
            
        Returns:
            Assistant's response
        """
        try:
            # Use simple LLM if no embeddings available
            if getattr(self, 'use_simple_llm', False) and hasattr(self, 'conversational_chain'):
                response = self.conversational_chain.invoke(
                    {"input": user_message},
                    config={"configurable": {"session_id": session_id}}
                )
                return response
            
            # Use RAG with retriever if available
            if hasattr(self, 'conversational_rag_chain') and not getattr(self, 'use_fallback', False):
                response = self.conversational_rag_chain.invoke(
                    {"input": user_message},
                    config={"configurable": {"session_id": session_id}}
                )
                return response
            else:
                return self._fallback_response(user_message)
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return self._fallback_response(user_message)
    
    def _fallback_response(self, user_message: str) -> str:
        """Fallback response using keyword matching"""
        user_message_lower = user_message.lower()
        
        if any(word in user_message_lower for word in ['blockchain', 'chain', 'crypto']):
            return self.fallback_responses.get('blockchain', 'This platform uses blockchain technology.')
        
        elif any(word in user_message_lower for word in ['course', 'learn', 'lesson']):
            return self.fallback_responses.get('courses', 'You can browse and enroll in courses.')
        
        elif any(word in user_message_lower for word in ['token', 'payment', 'pay']):
            return self.fallback_responses.get('tokens', 'Tokens are used for course access.')
        
        elif any(word in user_message_lower for word in ['certificate', 'nft', 'completion']):
            return self.fallback_responses.get('certificates', 'You receive NFT certificates upon completion.')
        
        elif any(word in user_message_lower for word in ['wallet', 'metamask', 'connect']):
            return self.fallback_responses.get('wallet', 'Connect your MetaMask wallet for blockchain features.')
        
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
