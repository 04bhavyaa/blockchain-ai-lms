"""
RAG Engine with LangChain 1.0+ (Updated imports)
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
import logging

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG Engine for course recommendations and Q&A"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=api_key,
            temperature=0.7
        )
        self.output_parser = StrOutputParser()
        self.embeddings = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
        self.vector_store = None
        self.retriever = None
    
    def process_documents(self, documents):
        """Process and index documents"""
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            
            splits = text_splitter.split_documents(documents)
            
            self.vector_store = FAISS.from_documents(
                splits,
                self.embeddings
            )
            
            self.retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 3}
            )
            
            logger.info(f"Processed {len(splits)} document chunks")
            return True
        except Exception as e:
            logger.error(f"Error processing documents: {str(e)}")
            return False
    
    def retrieve_context(self, query, k=3):
        """Retrieve relevant context from vector store"""
        try:
            if not self.vector_store:
                logger.warning("Vector store not initialized")
                return []
            
            results = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    def generate_response(self, query, context=None, chat_history=None):
        """Generate response using LLM with RAG"""
        try:
            # Build context string
            context_str = ""
            if context:
                context_str = "\n\n---\n\n".join(context)
            
            # Build messages from chat history
            messages = []
            if chat_history:
                for msg in chat_history:
                    if msg['role'] == 'user':
                        messages.append(HumanMessage(content=msg['content']))
                    elif msg['role'] == 'assistant':
                        messages.append(AIMessage(content=msg['content']))
            
            # Create prompt template
            if context_str:
                system_prompt = f"""You are a helpful LMS assistant. Answer questions about courses, 
learning progress, and educational topics based on the provided context.

CONTEXT:
{context_str}

Instructions:
- Answer based on the context provided
- Be concise and helpful
- If information is not in the context, say "I don't have information about this topic"
- Provide step-by-step guidance when needed"""
            else:
                system_prompt = """You are a helpful LMS assistant. Answer questions about courses,
learning progress, and educational topics.

Instructions:
- Be concise and helpful
- Provide step-by-step guidance when needed
- If you don't know, ask the user to contact support"""
            
            messages.insert(0, SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=query))
            
            # Generate response
            response = self.llm.invoke(messages)
            
            logger.info(f"Generated response for query: {query[:50]}...")
            return response.content
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Sorry, I couldn't generate a response. Please try again."
    
    def answer_faq(self, question, faqs):
        """Answer using FAQ database with similarity matching"""
        try:
            if not faqs:
                return None
            
            # Find best matching FAQ
            best_match = None
            best_score = 0
            
            for faq in faqs:
                # Calculate Jaccard similarity
                words_in_q = set(question.lower().split())
                words_in_faq = set(faq['question'].lower().split())
                
                if not (words_in_q | words_in_faq):
                    continue
                
                similarity = len(words_in_q & words_in_faq) / len(words_in_q | words_in_faq)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = faq
            
            # Return if similarity is high enough
            if best_match and best_score > 0.3:
                return best_match['answer']
            
            return None
        
        except Exception as e:
            logger.error(f"Error answering FAQ: {str(e)}")
            return None
    
    def summarize_conversation(self, messages):
        """Summarize conversation for context"""
        try:
            if not messages:
                return ""
            
            # Create summary prompt
            conv_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            
            summary_prompt = ChatPromptTemplate.from_messages([
                ("system", "Summarize the following conversation in 2-3 sentences:"),
                ("human", conv_text)
            ])
            
            chain = summary_prompt | self.llm | self.output_parser
            summary = chain.invoke({})
            
            return summary
        
        except Exception as e:
            logger.error(f"Error summarizing conversation: {str(e)}")
            return ""
