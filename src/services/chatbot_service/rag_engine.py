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

class SimpleRAGEngine:
    def __init__(self, qdrant_url: str, redis_url: str, document_path: str):
        """
        Initialize RAG with Qdrant and Gemini 2.5 Flash
        
        Args:
            qdrant_url: Qdrant connection URL (e.g., "http://localhost:6333")
            redis_url: Redis URL for chat history
            document_path: Path to your project documentation file
        """
        # Initialize Gemini embeddings and LLM
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.7
        )
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = "lms_docs"
        self.redis_url = redis_url
        
        # Create collection if not exists
        try:
            self.qdrant_client.get_collection(self.collection_name)
        except:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
        
        # Initialize vector store
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )
        
        # Load document on initialization
        self._load_document(document_path)
        
        # Setup RAG chain
        self._setup_chain()
    
    def _load_document(self, document_path: str):
        """Load and chunk the project documentation"""
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split document into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_text(content)
        
        # Add to Qdrant
        from langchain_core.documents import Document
        documents = [Document(page_content=chunk) for chunk in chunks]
        self.vector_store.add_documents(documents)
    
    def _setup_chain(self):
        """Setup the RAG chain with chat history"""
        # Retriever
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        # Prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant for a blockchain-powered Learning Management System.
            Use the following context to answer the user's question. If you don't know, say so.
            
            Context: {context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        # RAG chain
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.chain = (
            {
                "context": self.retriever | format_docs,
                "question": lambda x: x["question"],
                "chat_history": lambda x: x["chat_history"]
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    def chat(self, session_id: str, user_message: str) -> str:
        """
        Send message and get response with chat history
        
        Args:
            session_id: Unique session identifier
            user_message: User's question
            
        Returns:
            Assistant's response
        """
        # Get chat history from Redis
        message_history = RedisChatMessageHistory(
            session_id=session_id,
            url=self.redis_url
        )
        
        # Create chain with history
        chain_with_history = RunnableWithMessageHistory(
            self.chain,
            lambda session_id: message_history,
            input_messages_key="question",
            history_messages_key="chat_history"
        )
        
        # Get response
        response = chain_with_history.invoke(
            {"question": user_message},
            config={"configurable": {"session_id": session_id}}
        )
        
        return response
