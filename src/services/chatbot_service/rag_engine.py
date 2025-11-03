import os
import shutil
import textwrap
from typing import List, Dict, Any, TypedDict, Annotated
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
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

logger = logging.getLogger(__name__)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    session_id: str

class RAGEngine:
    def __init__(self, knowledge_base_queryset=None, chroma_db_dir=None, redis_url=None, google_api_key=None):
        self.knowledge_base_queryset = knowledge_base_queryset
        self.chroma_db_dir = chroma_db_dir or "chroma_db"
        self.redis_url = redis_url or "redis://localhost:6379"
        self.llm = None
        self.retriever = None
        self.vectorstore = None
        self.conversational_rag_chain = None
        self.langgraph_chatbot = None
        self.checkpointer = None

        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key

        self._initialize_rag_chain()
        self._initialize_langgraph_chatbot()

    def _load_knowledge_base_as_docs(self) -> List[Document]:
        if not self.knowledge_base_queryset:
            return []
        documents = []
        for kb_item in self.knowledge_base_queryset.filter(is_active=True):
            content = f"Title: {kb_item.title}\n\nContent: {kb_item.content}"
            metadata = {
                'source': kb_item.source,
                'doc_type': kb_item.doc_type,
                'id': str(kb_item.id)
            }
            documents.append(Document(page_content=content, metadata=metadata))
        return documents

    def _get_default_docs(self) -> List[Document]:
        content = """
        This is a Blockchain + AI-powered Learning Management System (LMS).
        Features:
        - Course management with modules and lessons
        - AI-powered recommendations and chatbot
        - Blockchain-verified certificates (NFTs)
        - Token-based rewards
        """
        metadata = {'source': 'system', 'doc_type': 'guide'}
        return [Document(page_content=textwrap.dedent(content), metadata=metadata)]

    def _initialize_rag_chain(self):
        documents = self._load_knowledge_base_as_docs() or self._get_default_docs()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        if os.path.exists(self.chroma_db_dir):
            shutil.rmtree(self.chroma_db_dir)
        os.makedirs(self.chroma_db_dir)
        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=self.chroma_db_dir
        )
        self.retriever = self.vectorstore.as_retriever()

        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7, max_tokens=2048)
        self.generate_response_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant for a Blockchain + AI-powered LMS.\nContext: {context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        self.rag_chain = (
            RunnablePassthrough.assign(
                context=(lambda x: x["input"]) | self.retriever | format_docs
            )
            | self.generate_response_prompt
            | self.llm
            | StrOutputParser()
        )
        self.conversational_rag_chain = RunnableWithMessageHistory(
            self.rag_chain,
            self._get_session_history_factory,
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def _get_session_history_factory(self, session_id: str):
        history = RedisChatMessageHistory(session_id=session_id, url=self.redis_url)
        return history

    def _initialize_langgraph_chatbot(self):
        self.checkpointer = MemorySaver()
        graph = StateGraph(ChatState)
        graph.add_node("retrieve_context", self._retrieve_context_node)
        graph.add_node("chat_node", self._chat_node)
        graph.add_edge(START, "retrieve_context")
        graph.add_edge("retrieve_context", "chat_node")
        graph.add_edge("chat_node", END)
        self.langgraph_chatbot = graph.compile(checkpointer=self.checkpointer)

    def _retrieve_context_node(self, state: ChatState) -> Dict[str, Any]:
        messages = state.get('messages', [])
        if not messages:
            return {'context': ''}
        latest_message = messages[-1]
        query = latest_message.content if isinstance(latest_message, HumanMessage) else state.get('context', '')
        docs = self.retriever.get_relevant_documents(query)
        context = "\n\n".join([doc.page_content for doc in docs])
        return {'context': context[:3000]}

    def _chat_node(self, state: ChatState) -> Dict[str, Any]:
        messages = state.get('messages', [])
        context = state.get('context', '')
        system_message = SystemMessage(
            content=f"""You are a helpful assistant for a Blockchain + AI-powered LMS.\nContext: {context}"""
        )
        full_messages = [system_message] + messages
        response = self.llm.invoke(full_messages)
        if not isinstance(response, AIMessage):
            response = AIMessage(content=str(response))
        return {'messages': [response]}

    def get_chat_response(self, query: str, session_id: str) -> str:
        input_messages = [HumanMessage(content=query)]
        result = self.langgraph_chatbot.invoke(
            {
                'messages': input_messages,
                'session_id': session_id,
                'context': ''
            },
            config={"configurable": {"thread_id": session_id}}
        )
        messages = result.get('messages', [])
        if messages:
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    return msg.content
        return "I couldn't generate a response."
