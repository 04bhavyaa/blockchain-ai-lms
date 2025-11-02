import os
import shutil
import textwrap
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Try to import langchain dependencies - make them optional
LANGCHAIN_AVAILABLE = False
try:
    from langchain_core.documents import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    from langchain_community.vectorstores import Chroma
    from langchain_community.chat_message_histories import RedisChatMessageHistory, ChatMessageHistory
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables.history import RunnableWithMessageHistory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain dependencies not available. RAG engine will use simple mode.")


class RAGEngine:
    """RAG Engine for LMS Chatbot - uses KnowledgeBase from database as context."""

    def __init__(self, knowledge_base_queryset=None, chroma_db_dir=None, redis_url=None, google_api_key=None):
        """
        Initialize RAG Engine with database knowledge base.
        
        Args:
            knowledge_base_queryset: Django QuerySet of KnowledgeBase objects (optional)
            chroma_db_dir: Directory for Chroma vectorstore (optional)
            redis_url: Redis URL for message history (optional)
            google_api_key: Google API Key for Gemini models (optional)
        """
        self.knowledge_base_queryset = knowledge_base_queryset
        self.chroma_db_dir = chroma_db_dir or "chroma_db"
        self.redis_url = redis_url or "redis://localhost:6379"
        self.langchain_available = LANGCHAIN_AVAILABLE
        self.llm = None
        self.retriever = None
        self.vectorstore = None
        self.conversational_rag_chain = None
        
        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key
        
        if self.langchain_available:
            try:
                self._initialize_rag_chain()
            except Exception as e:
                logger.error(f"Failed to initialize advanced RAG chain: {str(e)}")
                self.langchain_available = False
        else:
            logger.info("RAG Engine initialized in simple mode (no LangChain dependencies)")

    def _load_knowledge_base_as_docs(self) -> List[Document]:
        """Load knowledge base content from database as LangChain Documents."""
        if not self.knowledge_base_queryset:
            return []
        
        documents = []
        for kb_item in self.knowledge_base_queryset.filter(is_active=True):
            content = f"Title: {kb_item.title}\n\nContent: {kb_item.content}"
            metadata = {
                'source': kb_item.source,
                'doc_type': kb_item.doc_type,
                'id': str(kb_item.id) # Ensure metadata values are strings
            }
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents

    def _get_default_docs(self) -> List[Document]:
        """Returns default documents if knowledge base is empty."""
        logger.warning("No knowledge base documents found. RAG will use minimal context.")
        content = """
        This is a Blockchain + AI-powered Learning Management System (LMS).
        
        Features:
        - Course management with modules and lessons
        - AI-powered course recommendations
        - Blockchain-verified certificates (NFTs)
        - Token-based rewards system
        - Wallet integration for Web3 payments
        - Progress tracking and analytics
        
        Users can enroll in courses, complete lessons, earn tokens, and receive blockchain-verified certificates.
        Instructors can create courses, set token costs, and manage content.
        """
        metadata = {'source': 'system', 'doc_type': 'guide'}
        return [Document(page_content=textwrap.dedent(content), metadata=metadata)]

    def _initialize_rag_chain(self):
        """Initialize RAG chain with LangChain if available."""
        if not self.langchain_available:
            return

        try:
            # Load knowledge base from database
            documents = self._load_knowledge_base_as_docs()
            
            if not documents:
                documents = self._get_default_docs()
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)

            # Try to use embeddings and vectorstore if API key available
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                
                # --- FIX: Delete old DB to prevent stale data on restart ---
                # This assumes you want to rebuild from the queryset every time.
                # For production, you'd want an update/sync strategy.
                if os.path.exists(self.chroma_db_dir):
                    shutil.rmtree(self.chroma_db_dir)
                os.makedirs(self.chroma_db_dir)
                
                self.vectorstore = Chroma.from_documents(
                    documents=splits,
                    embedding=embeddings,
                    persist_directory=self.chroma_db_dir
                )
                self.retriever = self.vectorstore.as_retriever()
                logger.info(f"Initialized Chroma vector store with {len(splits)} document splits.")
                
            except Exception as e:
                logger.warning(f"Could not initialize embeddings/vectorstore: {e}. Using simple retrieval.")
                self.retriever = None

            # Try to use Gemini LLM if available
            try:
                # --- FIX: Corrected model name from 'gemini-2.0-flash' ---
                self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini LLM: {e}. Will use simple responses.")
                self.llm = None
                self.langchain_available = False # Can't run chain without LLM
                return

            if self.llm:
                # Prompt template
                self.generate_response_prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a helpful assistant for a Blockchain + AI-powered Learning Management System. "
                               "Use the provided context about courses, features, and the platform to answer questions. "
                               "If you don't know something, say you don't know. Be friendly and helpful."
                               "\nContext: {context}"),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                ])

                # RAG Chain using LCEL
                def format_docs(docs):
                    return "\n\n".join(doc.page_content for doc in docs)

                if self.retriever:
                    self.rag_chain = (
                        RunnablePassthrough.assign(
                            context=(lambda x: x["input"]) | self.retriever | format_docs
                        )
                        | self.generate_response_prompt
                        | self.llm
                        | StrOutputParser()
                    )
                else:
                    # Simple chain without vector retrieval (uses all docs as context)
                    def get_context(query):
                        # Use the unsplit documents as context
                        context = "\n\n".join([doc.page_content for doc in documents])
                        return context[:3000]  # Limit context length
                    
                    self.rag_chain = (
                        RunnablePassthrough.assign(
                            context=(lambda x: get_context(x["input"]))
                        )
                        | self.generate_response_prompt
                        | self.llm
                        | StrOutputParser()
                    )

                # RAG Chain with Redis message history (if available)
                try:
                    self.conversational_rag_chain = RunnableWithMessageHistory(
                        self.rag_chain,
                        self._get_session_history_factory,
                        input_messages_key="input",
                        history_messages_key="chat_history",
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize Redis message history: {e}")
                    self.conversational_rag_chain = self.rag_chain
                
                logger.info("RAG LCEL chain initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize RAG chain: {str(e)}")
            self.langchain_available = False

    def _get_session_history_factory(self, session_id: str):
        """
        Get session history from Redis.
        --- FIX: Falls back to in-memory history if Redis fails ---
        """
        try:
            # Test connection
            history = RedisChatMessageHistory(session_id=session_id, url=self.redis_url)
            history.add_user_message("test") # Simple test
            history.clear()
            logger.debug(f"Using Redis history for session {session_id}")
            return history
        except Exception as e:
            logger.warning(f"Redis connection failed for session {session_id}: {e}. Using in-memory history.")
            return ChatMessageHistory() # Return an empty, in-memory history object

    def get_chat_response(self, query: str, session_id: str) -> str:
        """Get chat response using RAG or simple fallback."""
        try:
            if self.langchain_available and self.conversational_rag_chain:
                response = self.conversational_rag_chain.invoke(
                    {"input": query},
                    config={"configurable": {"session_id": session_id}}
                )
                return response
            else:
                # Simple fallback response
                return self._simple_response(query)
        except Exception as e:
            logger.error(f"Failed to get chat response: {str(e)}")
            return self._simple_response(query)

    def _simple_response(self, query: str) -> str:
        """Simple response generator without LangChain."""
        query_lower = query.lower()
        
        # Get knowledge base context (load as simple dicts for this mode)
        kb_context = []
        if self.knowledge_base_queryset:
             kb_context = [
                 f"Title: {item.title}\nContent: {item.content}" 
                 for item in self.knowledge_base_queryset.filter(is_active=True)[:3]
            ]
        context_text = "\n\n".join(kb_context)

        # Simple keyword-based responses
        # --- FIX: Use textwrap.dedent to remove leading whitespace ---
        if any(word in query_lower for word in ['course', 'enroll', 'learn']):
            return textwrap.dedent(f"""
                I can help you with courses! Our platform offers courses in blockchain, AI, web development, and more. 
                
                You can browse courses, enroll in them, and track your progress. Some courses are free, while others require tokens or payment.

                Here's some info from our knowledge base:
                {context_text[:500]}

                Would you like to know more about a specific topic?""")
        
        elif any(word in query_lower for word in ['token', 'balance', 'reward']):
            return textwrap.dedent("""
                Our platform uses a token-based reward system. You can earn tokens by completing courses, lessons, and quizzes. 
                Tokens can be used to unlock premium courses or as rewards for your achievements.""")
        
        elif any(word in query_lower for word in ['certificate', 'nft', 'blockchain']):
            return textwrap.dedent("""
                When you complete a course, you can earn a blockchain-verified certificate minted as an NFT. 
                These certificates are permanently stored on the blockchain and can be verified by anyone.""")
        
        elif any(word in query_lower for word in ['wallet', 'metamask', 'connect']):
            return textwrap.dedent("""
                You can connect your Web3 wallet (like MetaMask) to enable blockchain features. 
                This allows you to make on-chain payments, receive NFT certificates, and interact with smart contracts.""")
        
        else:
            return textwrap.dedent(f"""
                I'm here to help with questions about our Blockchain + AI Learning Management System!
                
                Our platform offers:
                - Course management and learning paths
                - AI-powered recommendations
                - Blockchain-verified certificates
                - Token rewards system
                - Wallet integration

                Here's some info from our knowledge base:
                {context_text[:300]}

                What would you like to know more about?""")

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history from Redis for display."""
        messages = []
        if not self.langchain_available:
            return messages
            
        try:
            # --- FIX: Directly query Redis, don't use the factory ---
            history = RedisChatMessageHistory(session_id=session_id, url=self.redis_url)
            for message in history.messages:
                msg_dict = {
                    'type': 'human' if message.type == 'human' else 'ai',
                    'content': message.content,
                    # 'timestamp' is not a standard attribute on BaseMessage
                }
                messages.append(msg_dict)
        except Exception as e:
            logger.error(f"Failed to get chat history from Redis: {str(e)}")
        
        return messages

    def health(self):
        """Health check for RAG engine."""
        health_data = {
            "langchain_available": self.langchain_available,
            "mode": "advanced" if self.langchain_available else "simple",
        }
        
        if self.langchain_available and self.vectorstore:
            try:
                health_data["vectorstore_docs"] = self.vectorstore._collection.count()
            except Exception as e:
                health_data["vectorstore_docs"] = f"Error: {str(e)}"
        
        if self.llm:
            # --- FIX: Correct attribute is 'model_name' ---
            health_data["llm_model"] = getattr(self.llm, "model_name", "unknown")
        
        return health_data