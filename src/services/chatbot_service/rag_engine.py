import os
import shutil
from typing import List, Dict, Any, TypedDict, Annotated
import logging
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_community.chat_message_histories import RedisChatMessageHistory, ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    """State for the chat graph"""
    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    session_id: str


class RAGEngine:
    """
    RAG Engine using complete documents (no text splitting).
    Properly configured to use GOOGLE_API_KEY from .env file.
    """

    def __init__(self, knowledge_base_queryset=None, chroma_db_dir=None, redis_url=None, google_api_key=None):
        """
        Initialize RAG Engine

        Args:
            knowledge_base_queryset: Django QuerySet of KnowledgeBase objects
            chroma_db_dir: Directory for ChromaDB storage
            redis_url: Redis connection URL for chat history
            google_api_key: Google API key (if not provided, loads from .env)
        """
        self.knowledge_base_queryset = knowledge_base_queryset
        self.chroma_db_dir = chroma_db_dir or os.getenv('CHROMA_DB_DIR', 'chroma_db')
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')

        # Set Google API key - prioritize parameter, then environment variable
        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key
        elif not os.environ.get("GOOGLE_API_KEY"):
            # Try to load from .env if not already set
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                os.environ["GOOGLE_API_KEY"] = api_key
            else:
                raise ValueError(
                    "GOOGLE_API_KEY not found. "
                    "Please set it in your .env file or pass it as a parameter."
                )

        self.llm = None
        self.retriever = None
        self.vectorstore = None
        self.conversational_rag_chain = None
        self.langgraph_chatbot = None
        self.checkpointer = None

        logger.info("Initializing RAG Engine...")
        self._initialize_rag_chain()
        self._initialize_langgraph_chatbot()
        logger.info("RAG Engine initialized successfully")

    def _load_knowledge_base_as_docs(self) -> List[Document]:
        """Load knowledge base entries as complete documents (no splitting)"""
        if not self.knowledge_base_queryset:
            logger.warning("No knowledge base queryset provided")
            return []

        try:
            documents = []
            for kb_item in self.knowledge_base_queryset.filter(is_active=True):
                # Create complete document without splitting
                content = f"Title: {kb_item.title}\n\nContent: {kb_item.content}"

                metadata = {
                    'source': kb_item.source,
                    'doc_type': kb_item.doc_type,
                    'id': str(kb_item.id),
                    'title': kb_item.title,
                    'tags': kb_item.tags or '',
                }

                documents.append(Document(page_content=content, metadata=metadata))

            logger.info(f"Loaded {len(documents)} complete documents from knowledge base")
            return documents

        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return []

    def _get_default_docs(self) -> List[Document]:
        """Provide default system documentation"""
        docs = [
            Document(
                page_content="""Title: Blockchain AI LMS Overview

This is a Blockchain-powered AI Learning Management System that combines modern education with Web3 technology.

Key Features:
- Course Management: Create and manage courses with modules and lessons
- AI-Powered Chatbot: Get instant answers about courses and content
- Blockchain Certificates: Earn verifiable NFT certificates upon course completion
- Token Rewards: Earn tokens for completing courses and achieving milestones
- Smart Recommendations: AI suggests courses based on your learning history
- Secure Transactions: All certificates and tokens are blockchain-verified

How to Get Started:
1. Browse available courses
2. Enroll in courses that interest you
3. Complete lessons and modules
4. Earn certificates and tokens
5. Track your progress on the dashboard""",
                metadata={'source': 'system', 'doc_type': 'guide', 'title': 'Platform Overview'}
            ),
            Document(
                page_content="""Title: How to Use the AI Chatbot

The AI chatbot is your personal learning assistant that can help you with:

Questions You Can Ask:
- "What courses are available?"
- "How do I earn certificates?"
- "Tell me about blockchain features"
- "How do tokens work?"
- "What are the course prerequisites?"
- "How do I track my progress?"

The chatbot uses information from our knowledge base to provide accurate, helpful responses. 
If you have a question about the platform, courses, or features, just ask!""",
                metadata={'source': 'system', 'doc_type': 'guide', 'title': 'Chatbot Guide'}
            ),
        ]

        logger.info("Using default system documentation")
        return docs

    def _initialize_rag_chain(self):
        """Initialize the RAG chain with vector store and retriever"""
        try:
            # Load documents without splitting
            documents = self._load_knowledge_base_as_docs() or self._get_default_docs()

            logger.info(f"Initializing RAG with {len(documents)} complete documents")

            # Initialize embeddings with explicit API key from environment
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=os.environ.get("GOOGLE_API_KEY")
            )

            # Clear and recreate ChromaDB directory
            if os.path.exists(self.chroma_db_dir):
                shutil.rmtree(self.chroma_db_dir)
            os.makedirs(self.chroma_db_dir, exist_ok=True)

            # Create vector store with complete documents
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=embeddings,
                persist_directory=self.chroma_db_dir
            )

            # Create retriever - get top 3 most relevant complete documents
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )

            # Initialize LLM with explicit API key
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.7,
                max_output_tokens=2048,
                google_api_key=os.environ.get("GOOGLE_API_KEY")
            )

            # Create prompt template
            self.generate_response_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful AI assistant for a Blockchain-powered Learning Management System.

Use the following context to answer the user's question. If the context doesn't contain enough information, use your general knowledge about LMS and education platforms, but clearly indicate when you're doing so.

Context:
{context}

Guidelines:
- Be friendly, helpful, and encouraging
- Provide clear, concise answers
- If asked about courses, certificates, or tokens, refer to the context
- For technical questions, be specific and accurate
- If you're unsure, admit it and suggest where to find more information"""),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ])

            def format_docs(docs):
                """Format retrieved documents into context string"""
                if not docs:
                    return "No specific context available."

                formatted = []
                for i, doc in enumerate(docs, 1):
                    title = doc.metadata.get('title', 'Document')
                    formatted.append(f"[Document {i}: {title}]\n{doc.page_content}")

                return "\n\n---\n\n".join(formatted)

            # Create RAG chain
            self.rag_chain = (
                RunnablePassthrough.assign(
                    context=(lambda x: x["input"]) | self.retriever | format_docs
                )
                | self.generate_response_prompt
                | self.llm
                | StrOutputParser()
            )

            # Wrap with message history
            self.conversational_rag_chain = RunnableWithMessageHistory(
                self.rag_chain,
                self._get_session_history_factory,
                input_messages_key="input",
                history_messages_key="chat_history",
            )

            logger.info("RAG chain initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing RAG chain: {e}", exc_info=True)
            raise

    def _get_session_history_factory(self, session_id: str):
        """Get or create chat history for a session"""
        try:
            history = RedisChatMessageHistory(session_id=session_id, url=self.redis_url)
            return history
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory history.")
            return ChatMessageHistory()

    def _initialize_langgraph_chatbot(self):
        """Initialize LangGraph-based chatbot with state management"""
        try:
            self.checkpointer = MemorySaver()
            graph = StateGraph(ChatState)

            # Add nodes
            graph.add_node("retrieve_context", self._retrieve_context_node)
            graph.add_node("chat_node", self._chat_node)

            # Add edges
            graph.add_edge(START, "retrieve_context")
            graph.add_edge("retrieve_context", "chat_node")
            graph.add_edge("chat_node", END)

            # Compile graph
            self.langgraph_chatbot = graph.compile(checkpointer=self.checkpointer)
            logger.info("LangGraph chatbot initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing LangGraph chatbot: {e}", exc_info=True)
            raise

    def _retrieve_context_node(self, state: ChatState) -> Dict[str, Any]:
        """Node to retrieve relevant context from vector store"""
        messages = state.get('messages', [])
        if not messages:
            return {'context': ''}

        # Get latest user message
        latest_message = messages[-1]
        query = latest_message.content if isinstance(latest_message, HumanMessage) else ''

        if not query:
            return {'context': ''}

        try:
            # Retrieve relevant documents
            docs = self.retriever.invoke(query)

            # Format context from complete documents
            context_parts = []
            for doc in docs:
                title = doc.metadata.get('title', 'Document')
                context_parts.append(f"[{title}]\n{doc.page_content}")

            context = "\n\n---\n\n".join(context_parts)

            # Limit context size to avoid token limits
            return {'context': context[:4000]}

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {'context': ''}

    def _chat_node(self, state: ChatState) -> Dict[str, Any]:
        """Node to generate chat response"""
        messages = state.get('messages', [])
        context = state.get('context', '')

        # Create system message with context
        system_content = """You are a helpful AI assistant for a Blockchain-powered Learning Management System.

Use the following context from our knowledge base to provide accurate responses:

{context}

If the context is empty or insufficient, use your general knowledge but let the user know."""

        system_message = SystemMessage(content=system_content.format(context=context))

        # Combine system message with chat history
        full_messages = [system_message] + messages

        try:
            # Generate response
            response = self.llm.invoke(full_messages)

            if not isinstance(response, AIMessage):
                response = AIMessage(content=str(response))

            return {'messages': [response]}

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return {
                'messages': [AIMessage(
                    content="I apologize, but I encountered an error processing your message. Please try again."
                )]
            }

    def get_chat_response(self, query: str, session_id: str) -> str:
        """
        Get chat response for a user query

        Args:
            query: User's question
            session_id: Session identifier for conversation history

        Returns:
            AI-generated response string
        """
        input_messages = [HumanMessage(content=query)]

        try:
            # Invoke LangGraph chatbot
            result = self.langgraph_chatbot.invoke(
                {
                    'messages': input_messages,
                    'session_id': session_id,
                    'context': ''
                },
                config={"configurable": {"thread_id": session_id}}
            )

            # Extract AI response
            messages = result.get('messages', [])
            if messages:
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage):
                        return msg.content

            return "I couldn't generate a response. Please try rephrasing your question."

        except Exception as e:
            logger.error(f"Error in get_chat_response: {e}", exc_info=True)
            return "I apologize, but I encountered an error. Please try again later."

    def refresh_knowledge_base(self):
        """Refresh the vector store with latest knowledge base entries"""
        logger.info("Refreshing knowledge base...")
        try:
            self._initialize_rag_chain()
            logger.info("Knowledge base refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing knowledge base: {e}")
            raise

    def search_knowledge_base(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search knowledge base and return results

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of search results with metadata
        """
        try:
            docs = self.vectorstore.similarity_search(query, k=k)

            results = []
            for doc in docs:
                results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'title': doc.metadata.get('title', 'Untitled'),
                    'source': doc.metadata.get('source', 'Unknown'),
                })

            return results

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []