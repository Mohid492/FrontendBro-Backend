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
model="qwen3:14b"
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
    # Always fetch ALL chunks from Tailwind sources
    tailwind_docs = vector_store.get(
        where={"source": "Tailwind"}, include=["documents"]
    )["documents"]

    tailwind_context = "\n".join(tailwind_docs)

    tailwind_ui_kit = vector_store.get(where={"source": "Tailwind-UI-Kit"}, include=["documents"])["documents"]
    tailwind_templates = vector_store.get(where={"source": "Tailwindcss-Templates"}, include=["documents"])["documents"]

    styling_examples = "\n".join(tailwind_ui_kit + tailwind_templates)

    # Fetch top-k matches for user prompt from other docs
    relevant_docs = vector_store.similarity_search(
        query=prompt,
        k=5,
        filter={"source": {"$nin": ["Tailwind", "Tailwind-UI-Kit", "Tailwindcss-Templates"]}}
    )
    other_context = "\n".join([doc.page_content for doc in relevant_docs])
    context = f"""
    [TAILWIND CSS DOCS — Always use for actual utility classes & responsive design]
    {tailwind_context}

    [STYLING REFERENCE — UI Kit & Templates, use only as design inspiration]
    {styling_examples}

    [OTHER RELEVANT DOCS — React, Router, Axios, RHF]
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
    You are an **expert Senior React Developer** and **TailwindCSS specialist**.

    ## PURPOSE
    Generate a **fully functional, production-ready React application** that strictly follows:
    - Styling rules from **[TAILWIND CSS DOCS]**
    - Layout inspiration from **[STYLING REFERENCE]** (inspiration only — DO NOT copy code)
    - Logic, routing, and data handling from **[OTHER RELEVANT DOCS]**

    The agent reads documentation from a vector store (`{context}`) and responds to user requirements (`{prompt}`).

    ---

    ## OUTPUT ARCHITECTURE (MANDATORY)
    - `src/components/` → Reusable UI components (e.g., `Navbar.jsx`, `ProductCard.jsx`)
    - `src/pages/` → Page-level components (e.g., `ProductPage.jsx`, `CartPage.jsx`)
    - `src/context/` → Context provider for shared state (`CartContext.jsx`)
    - `src/App.jsx` → Main router shell only (imports Navbar + Pages)
    - `src/index.jsx` → React DOM entry point

    ---

    ## RULES
    1. **Coding Style**
       - Functional components with Hooks only.
       - All styling uses Tailwind utility classes.
       - Code must compile without errors.

    2. **Routing**
       - Use `react-router-dom` for navigation between pages.
       - Include installation commands for any new packages at the start.

    3. **State Management**
       - Use React Context API for cart state.
       - Allow adding the same product multiple times; dynamically calculate total.

    ---

    ## VECTOR CONTEXT
    Only include details from `{context}` if relevant; ignore unrelated vector content.

    ---

    ## OUTPUT FORMAT
    - **Section 1:** Installation commands
    - **Section 2:** Complete file tree with **file names and code blocks per file**
    - **Section 3:** Notes on responsive behavior, accessibility, and design decisions

    ---

    ## CONTEXT
    Previous Chat:
    {prev_messages_text}

    User Requirement:
    {prompt}
    """

    # Query DeepSeek model
    response =await llm.ainvoke(final_prompt)
    logger.info("LLM called")
    logger.info(f"Context Length: {len(context)} characters")
    chat_history.add_user_message(prompt)
    chat_history.add_ai_message(str(response))    # Store new messages ad
    return response
