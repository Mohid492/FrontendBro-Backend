import os
from ..config import settings
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings,OllamaLLM
from langchain.memory import ConversationSummaryBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()


redis_url=settings.REDIS_URL
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
model="deepseek-coder-v2:latest"
llm = OllamaLLM(model=model)
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "RAG", "db", "chroma_db"))

async def deepseek_agent(prompt:str,session_id: str):
    if not os.path.exists(persistent_directory):
        return "No vector database found. Please generate vectors first."
    # loading the vector db
    vector_store = Chroma(
        persist_directory=persistent_directory,
        embedding_function=embeddings,
    )
    all_docs=vector_store.get(include=['documents'])['documents']
    print(f'Found {len(all_docs)} relevant documents for the query.')
    if not all_docs:
        return "No relevant documents found."
    context = "\n".join(all_docs)

    chat_history = RedisChatMessageHistory(session_id=session_id, url=redis_url)

    memory = ConversationSummaryBufferMemory(
        llm=llm,
        memory_key="chat_history",
        chat_memory=chat_history,
        max_token_limit=1500,  # adjust based on model context size
        return_messages=True
    )
    # fetch previous messages from chat history
    prev_messages = await memory.chat_memory.aget_messages()
    if prev_messages:
        if len(prev_messages)>=3:
            prev_messages= prev_messages[-3:] if len(prev_messages)>3 else prev_messages
        prev_messages_text = "\n".join(
            [f"{msg.type.upper()}: {msg.content}" for msg in prev_messages]
        )
        logger.info("Previous messages fetched from chat history:")
        logger.info(prev_messages_text)
    else:
        prev_messages_text = None

    final_prompt = f"""
    You are a senior React developer and TailwindCSS expert.  
    Your goal is to generate a **fully working, production-ready React application** (or component) based exclusively on the documentation and code snippets provided in the Context section.  

    You must:
    - Use only the imports, APIs, and patterns found in Context.  
    - Produce all necessary files and folder structure, including:
      - package.json (with required dependencies)  
      - tailwind.config.js and postcss.config.js (with Tailwind setup)  
      - src/index.jsx  
      - src/App.jsx  
      - src/components/... (one component per file, default export)    
    - Ensure the code **compiles without errors** and follows best practices:
      - Functional components with hooks only  
      - Default exports for all components  
      - Mobile-first responsive design using Tailwind classes  
      - Accessibility (alt tags, semantic HTML)  
      - No unused imports or dead code  
    - The app must use TailwindCSS for **all styling** (no inline styles unless absolutely necessary).  
    - Wrap your answer in Markdown triple backtick code blocks per file, with file paths as headings.  
    Do NOT use Vue.js. Only use React and TailwindCSS as shown in the context.
    Remember in context even if the code is in js or ts or tsx, you have to generate the code in jsx format.
    For the ease of users you also provide installation commands for the dependencies.
    Previous Chat History:  
    {prev_messages_text}  

    Context:  
    {context}  

    User Question:  
    {prompt}  
    """

    # Query DeepSeek model
    response =await llm.ainvoke(final_prompt)
    chat_history.add_user_message(prompt)
    chat_history.add_ai_message(str(response))    # Store new messages ad
    return response
