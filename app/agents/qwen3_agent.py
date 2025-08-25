import os
from ..config import settings
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings,OllamaLLM,ChatOllama
from langchain.memory import ConversationSummaryBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()


redis_url=settings.REDIS_URL
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

model="qwen3:30b"
llm = ChatOllama(model=model)
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "RAG", "db", "chroma_db"))

async def qwen_agent(prompt:str, session_id: str):
    if not os.path.exists(persistent_directory):
        return "No vector database found. Please generate vectors first."
    # loading the vector db
    vector_store = Chroma(
        persist_directory=persistent_directory,
        embedding_function=embeddings,
    )

    tailwind_ui_kit = vector_store.get(where={"source": "Tailwind-UI-Kit"}, include=["documents"])["documents"]
    tailwind_templates = vector_store.get(where={"source": "Tailwindcss-Templates"}, include=["documents"])["documents"]

    styling_examples = "\n".join(tailwind_ui_kit + tailwind_templates)

    # Fetch top-k matches for user prompt from other docs
    relevant_docs = vector_store.similarity_search(
        query=prompt,
        k=6,
        filter={"source": {"$nin": ["Tailwind-UI-Kit", "Tailwindcss-Templates"]}}
    )
    other_context = "\n".join([doc.page_content for doc in relevant_docs])
    context = f"""
    [STYLING REFERENCE — UI Kit & Templates, use only as design inspiration]
    {styling_examples}

    [OTHER RELEVANT DOCS — React,Tailwindcss , Router, Axios]
    {other_context}
    """

    chat_history = RedisChatMessageHistory(session_id=session_id, url=redis_url)

    memory = ConversationSummaryBufferMemory(
        llm=llm,
        memory_key="chat_history",
        chat_memory=chat_history,
        max_token_limit=2500,  # adjust based on model context size
        return_messages=True
    )
    #fetch previous messages from chat history
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
    You are a Senior React + TailwindCSS engineer. Output a complete, production-ready React app.
        
        PURPOSE
        - Build a single-product e-commerce site with cart (add same item multiple times, compute totals), routing, and responsive UI with Tailwind.
        
        ALLOWED ROOT FILES
        - package.json, vite.config.js, index.html
        - tailwind.config.js, postcss.config.js
        - src/index.css containing ONLY @tailwind directives
        
        ARCHITECTURE
        - src/components/ → reusable UI (Navbar.jsx, ProductCard.jsx, etc.)
        - src/pages/ → page-level (ProductPage.jsx, CartPage.jsx)
        - src/context/ → shared state provider (CartContext.jsx)
        - src/App.jsx → router shell importing Navbar + pages
        - src/index.jsx → React DOM entry
        - Root configs listed above are mandatory
        
        HARD BANS INSIDE src/
        - No <script> tags, CDN links, or inline <style>
        - No TypeScript files
        - No CSS files other than src/index.css, and that file must only contain @tailwind directives
        
        RULES
        1) Coding Style
           - Functional components with hooks only
           - All styling via Tailwind utility classes
        2) Routing
           - Use react-router-dom
        3) State Management
           - React Context for cart
        4) Tailwind
           - Responsive prefixes (sm, md, lg, xl)
        5) Data
           - No external APIs; use local mock data. If there are no HTTP calls, do NOT import axios.
        6) Build
           - Use Vite + React. Provide package.json scripts and vite.config.js.
           - Provide index.html (needed by Vite)
        
        VECTOR CONTEXT (reference only; ignore if irrelevant)
        {context}
        
        OUTPUT FORMAT
        - Section 1: Installation commands
        - Section 2: Complete file tree with one fenced code block per file
          - First line of each block: FILE: <relative-path-from-project-root>
          - Then the full file contents only
        - Section 3: Notes on responsive behavior, accessibility, and design decisions (max 3 sentences)
        
        PREFLIGHT CHECKLIST (self-verify before output; if any fail, silently fix then output)
        - package.json, vite.config.js, index.html, tailwind.config.js, postcss.config.js, src/index.css exist
        - src/index.jsx renders <App/> into #root
        - src/App.jsx defines BrowserRouter with routes for product and cart
        - src/context/CartContext.jsx exports provider and hook; totals compute correctly
        - All imports resolve, all files referenced exist, no TypeScript, no external API calls
        - Only src/index.css contains @tailwind directives; no other CSS files
        - Build runs with: npm i && npm run dev
        
        Chat History:
        {prev_messages_text}
        
        USER REQUIREMENT
        {prompt}
        
        
        IMPORTANT
        - Complete, executable app only. No explanations.

    """

    # Query DeepSeek model
    logger.info("LLM called")
    logger.info(f"Context Length: {len(context)} characters")
    response =await llm.ainvoke(final_prompt)
    chat_history.add_user_message(prompt)
    chat_history.add_ai_message(str(response.content))    # Store new messages ad
    logger.info("Chat stored in redis")
    if hasattr(response, "content"):
        return response.content
    return str(response)
