import os
from ..config import settings
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings,OllamaLLM,ChatOllama
from langchain.memory import ConversationSummaryBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_openai import ChatOpenAI
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()


redis_url=settings.REDIS_URL
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

llm=ChatOpenAI(
    model="gpt-5-mini",
    api_key=settings.OPENAI_API_KEY
)
# If you want to use Ollama model, uncomment below and comment above llm
#llm = ChatOllama(model="deepseek-r1:8b")

current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "RAG", "db", "chroma_db"))

async def code_agent(prompt:str, session_id: str):
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

    [OTHER RELEVANT DOCS — React,Tailwindcss , React Router, Axios]
    {other_context}
    """

    chat_history = RedisChatMessageHistory(session_id=session_id, url=redis_url)

    memory = ConversationSummaryBufferMemory(
        llm=llm,
        memory_key="chat_history",
        chat_memory=chat_history,
        max_token_limit=3500,
        return_messages=True
    )

    prev_messages = await memory.chat_memory.aget_messages()
    if prev_messages:
        if len(prev_messages) >= 2:
            prev_messages = prev_messages[-2:] if len(prev_messages) >= 2 else prev_messages
        prev_messages_text = "\n".join(
            [f"{msg.type.upper()}: {msg.content}" for msg in prev_messages]
        )
        logger.info("Previous messages fetched from chat history:")

    else:
        prev_messages_text = None

    final_prompt = f"""
            You are a Senior React + TailwindCSS engineer. Output a complete, production-ready React app based on the USER REQUIREMENT. Use .jsx file extensions for all React components and JavaScript files containing React code.

            PURPOSE
            - Build a fully functional, responsive webpage/app as described in the USER REQUIREMENT, using React and Tailwind CSS.
            - Incorporate features like state management, routing, and UI components as needed to fulfill the requirement.

            ARCHITECTURE (adapt based on USER REQUIREMENT; use these as defaults if suitable)
            - src/components/ → reusable UI components (e.g., Navbar.jsx, Button.jsx)
            - src/pages/ → page-level components (e.g., HomePage.jsx, AboutPage.jsx)
            - src/context/ → shared state providers if needed (e.g., AppContext.jsx for global state)
            - src/App.jsx → main app shell with router and layout (import shared components/pages)
            - src/index.jsx → React DOM entry
            - Root configs (package.json, vite.config.js, index.html, src/index.css) are mandatory

            HARD BANS INSIDE src/
            - No <script> tags, CDN links, or inline <style>
            - No TypeScript files (use .jsx for React components, .js for non-React if needed)
            - No CSS files other than src/index.css, and that file must only contain @tailwind directives
            - No external API calls or imports (e.g., no axios); use local mock data if data is needed

            RULES
            1) Coding Style
               - Functional components with hooks only (e.g., useState, useEffect, useContext)
               - All styling via Tailwind utility classes; ensure responsive design with prefixes (sm, md, lg, xl)
            2) Routing
               - Use react-router-dom if multiple pages/routes are required by the USER REQUIREMENT
            3) State Management
               - Use React Context for shared/global state if needed; local state with hooks otherwise
            4) Data
               - No external APIs; hardcode mock data in components or context as appropriate
            5) Build
               - Use Vite + React setup. Provide package.json with scripts (e.g., npm run dev, build) and vite.config.js.
               - Provide index.html (needed by Vite)

            VECTOR CONTEXT (reference only; integrate relevant ideas/code patterns if they match the USER REQUIREMENT, ignore if irrelevant)
            {context}

            OUTPUT FORMAT
            - Section 1: Installation commands (e.g., npm init vite@latest, dependencies)
            - Section 2: Complete file tree with one fenced code block per file
              - First line of each block: FILE: <relative-path-from-project-root>
              - Then the full file contents only (ensure all imports resolve and code is error-free)
            - Section 3: Notes on responsive behavior, accessibility, and design decisions (max 3 sentences)

            PREFLIGHT CHECKLIST (self-verify before output; if any fail, silently fix then output)
            - src/index.jsx renders <App/> into #root
            - src/App.jsx sets up BrowserRouter with routes if routing is needed, and imports all necessary components/pages
            - Any context (if used) exports provider and hook; state logic is correct and bug-free
            - All imports resolve, all files referenced exist, no TypeScript, no external API calls, app fulfills USER REQUIREMENT; all React files use .jsx extension
            - Only src/index.css contains @tailwind directives; no other CSS files
            - Build runs with: npm i && npm run dev; code is complete and executable without errors

            CHAT HISTORY
            {prev_messages_text}
            USER REQUIREMENT
            {prompt}

            IMPORTANT
            - Complete, executable app only. No explanations outside the output format.
        """

    # Query DeepSeek model
    logger.info("LLM called")
    logger.info(f"Context Length: {len(context)} characters")
    response =await llm.ainvoke(final_prompt)
    chat_history.add_user_message(prompt)
    chat_history.add_ai_message(str(response.content))
    logger.info("Chat stored in redis")
    if hasattr(response, "content"):
        return response.content
    return str(response)


async def image_to_code_agent(image:str,prompt:str,session_id:str):
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

    [OTHER RELEVANT DOCS — React,Tailwindcss , React Router, Axios]
    {other_context}
    """

    chat_history = RedisChatMessageHistory(session_id=session_id, url=redis_url)

    memory = ConversationSummaryBufferMemory(
        llm=llm,
        memory_key="chat_history",
        chat_memory=chat_history,
        max_token_limit=3500,
        return_messages=True
    )

    prev_messages = await memory.chat_memory.aget_messages()
    if prev_messages:
        if len(prev_messages) >= 2:
            prev_messages = prev_messages[-2:] if len(prev_messages) >= 2 else prev_messages
        prev_messages_text = "\n".join(
            [f"{msg.type.upper()}: {msg.content}" for msg in prev_messages]
        )
        logger.info("Previous messages fetched from chat history:")

    else:
        prev_messages_text = None

    image_data = base64.b64encode(image).decode("utf-8")

    final_prompt = f"""
                You are a Senior React + TailwindCSS engineer. Output a complete, production-ready React app based on the USER REQUIREMENT. Use .jsx file extensions for all React components and JavaScript files containing React code.
                First you need to check if the image that is provided to you is image of webpage,webapp,app if not then only tell user that Please enter a valid image else move on.You will generate the code based on the image and user requirement.
                PURPOSE
                - Build a fully functional, responsive webpage/app as described in the USER REQUIREMENT, using React and Tailwind CSS.
                - Incorporate features like state management, routing, and UI components as needed to fulfill the requirement.

                ARCHITECTURE (adapt based on USER REQUIREMENT; use these as defaults if suitable)
                - src/components/ → reusable UI components (e.g., Navbar.jsx, Button.jsx)
                - src/pages/ → page-level components (e.g., HomePage.jsx, AboutPage.jsx)
                - src/context/ → shared state providers if needed (e.g., AppContext.jsx for global state)
                - src/App.jsx → main app shell with router and layout (import shared components/pages)
                - src/index.jsx → React DOM entry
                - Root configs (package.json, vite.config.js, index.html, src/index.css) are mandatory

                HARD BANS INSIDE src/
                - No <script> tags, CDN links, or inline <style>
                - No TypeScript files (use .jsx for React components, .js for non-React if needed)
                - No CSS files other than src/index.css, and that file must only contain @tailwind directives
                - No external API calls or imports (e.g., no axios); use local mock data if data is needed

                RULES
                1) Coding Style
                   - Functional components with hooks only (e.g., useState, useEffect, useContext)
                   - All styling via Tailwind utility classes; ensure responsive design with prefixes (sm, md, lg, xl)
                2) Routing
                   - Use react-router-dom if multiple pages/routes are required by the USER REQUIREMENT
                3) State Management
                   - Use React Context for shared/global state if needed; local state with hooks otherwise
                4) Data
                   - No external APIs; hardcode mock data in components or context as appropriate
                5) Build
                   - Use Vite + React setup. Provide package.json with scripts (e.g., npm run dev, build) and vite.config.js.
                   - Provide index.html (needed by Vite)

                VECTOR CONTEXT (reference only; integrate relevant ideas/code patterns if they match the USER REQUIREMENT, ignore if irrelevant)
                {context}

                OUTPUT FORMAT
                - Section 1: Installation commands (e.g., npm init vite@latest, dependencies)
                - Section 2: Complete file tree with one fenced code block per file
                  - First line of each block: FILE: <relative-path-from-project-root>
                  - Then the full file contents only (ensure all imports resolve and code is error-free)
                - Section 3: Notes on responsive behavior, accessibility, and design decisions (max 3 sentences)

                PREFLIGHT CHECKLIST (self-verify before output; if any fail, silently fix then output)
                - src/index.jsx renders <App/> into #root
                - src/App.jsx sets up BrowserRouter with routes if routing is needed, and imports all necessary components/pages
                - Any context (if used) exports provider and hook; state logic is correct and bug-free
                - All imports resolve, all files referenced exist, no TypeScript, no external API calls, app fulfills USER REQUIREMENT; all React files use .jsx extension
                - Only src/index.css contains @tailwind directives; no other CSS files
                - Build runs with: npm i && npm run dev; code is complete and executable without errors
                
                ## IMAGE
                {image_data}
                CHAT HISTORY
                {prev_messages_text}
                USER REQUIREMENT
                {prompt}

                IMPORTANT
                - Complete, executable app only. No explanations outside the output format.
            """

    # Query DeepSeek model
    logger.info("LLM called")
    logger.info(f"Context Length: {len(context)} characters")
    response = await llm.ainvoke(final_prompt)
    chat_history.add_user_message(prompt)
    chat_history.add_ai_message(str(response.content))
    logger.info("Chat stored in redis")
    if hasattr(response, "content"):
        return response.content
    return str(response)
