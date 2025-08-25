from langchain_ollama import ChatOllama
import imghdr
import base64
import logging
import os
from ..config import settings
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings,OllamaLLM
from langchain.memory import ConversationSummaryBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory


# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()
# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()

model="gemma3:12b"
redis_url=settings.REDIS_URL
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
llm= ChatOllama(model=model)
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, "db")
persistent_directory = os.path.abspath(os.path.join(current_dir, "..", "RAG", "db", "chroma_db"))


async def gemma_agent(image, session_id:str, prompt:str=None):

    if not os.path.exists(persistent_directory):
        return "No vector database found. Please generate vectors first."

    image_data = base64.b64encode(image).decode("utf-8")

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
        if len(prev_messages) >= 3:
            prev_messages = prev_messages[-3:] if len(prev_messages) > 3 else prev_messages
        prev_messages_text = "\n".join(
            [f"{msg.type.upper()}: {msg.content}" for msg in prev_messages]
        )
        logger.info("Previous messages fetched from chat history:")
        logger.info(prev_messages_text)
    else:
        prev_messages_text = None

    final_prompt = f"""
        You are an **expert Senior React Developer** and **TailwindCSS specialist**.  
        First you need to check if the image that is provided to you is image of webpage,webapp,app if not then only tell user that Please enter a valid image else move on.You wil generate exact webpage or website as given in the image.
        Your goal is to generate a **fully functional, production‑ready React application** that strictly adheres to the following guidelines.
        ## PURPOSE
        Generate a **fully functional, production‑ready React application** that strictly follows:
        - Styling rules from **[TAILWIND CSS DOCS — ALWAYS use for actual utility classes & responsive design]**
        - Layout inspiration from **[STYLING REFERENCE — UI Kit & Templates, use only as design inspiration]**
        - Logic, routing, and data handling from **[OTHER RELEVANT DOCS — React, Router, Axios, RHF]**
        - Output a complete file tree, with each component, context, and page in its own file (e.g., `Navbar.jsx`, `CartContext.jsx`, `ProductPage.jsx`).
        - Use React Context API for any state shared across multiple components (e.g., cart state).
        - All code must be split into separate files as per the architecture below.

        ## ARCHITECTURE (MANDATORY)
        - `src/components/` → Reusable UI components (e.g., `Navbar.jsx`, `ProductCard.jsx`)
        - `src/pages/` → Page‑level components (e.g., `ProductPage.jsx`, `CartPage.jsx`)
        - `src/context/` → Context provider for shared state (`CartContext.jsx`)
        - `src/App.jsx` → Main router shell only (imports Navbar + Pages)
        - `src/index.jsx` → React DOM entry point


        ## RULES (ABSOLUTELY CRITICAL)
        1. **Coding Style:**
           - Functional components with Hooks only.  No class components.
           - All styling *must* use Tailwind utility classes.  No custom CSS, CSS modules, or inline styles.
           - Code must compile without errors.  Maintain consistent formatting.

        2. **Routing:**
           - Use `react-router-dom` for navigation between pages.
           - Include installation commands for any new packages at the start.

        3. **State Management:**
           - Use React Context API for cart state.
           - Allow adding the same product multiple times; dynamically calculate total.

        4. **TailwindCSS Adherence:**
           - *Strictly* follow the [TAILWIND CSS DOCS]. Use only utility classes – no overrides.
           - Responsive design must be implemented using Tailwind's responsive prefixes (`sm`, `md`, `lg`, `xl`).

        5. **Reasoning:**
           - Apply logical thinking and best practices to solve problems and structure the code.
           - Ensure all solutions are robust, efficient, and follow modern development standards.

        ## VECTOR CONTEXT (ONLY FOR REFERENCE – Prioritize TAILWIND CSS DOCS)
        Only include details from `{{context}}` if relevant; ignore unrelated vector content.

        ## OUTPUT FORMAT
        - **Section 1:** Installation commands (using `npm install` or `yarn add`)
        - **Section 2:** Complete file tree with **file names and code blocks per file**  
          - Each file must be in its own fenced code block.  
          - First line inside each block must be exactly:  
            FILE: <relative-path-from-project-root>  
          - Then the full file contents, nothing else.
        - **Section 3:** Notes on responsive behavior, accessibility, and design decisions (brief – max 3 sentences)

        ## VECTOR CONTEXT
        {context}

        ## DO NOT FORGET — CRITICAL RULES:
        - Follow architecture exactly
        - Tailwind utility classes only
        - React Router for nav
        - React Context API for shared state
        - Output format: Section 1 installs, Section 2 file tree/code, Section 3 notes
        - No comments or TODOs in any file
        - No external APIs or placeholders — use local mock data if needed
        - No using typescript
        - Use axios for any api calls

        Chat History:
        {prev_messages_text}
        
        ## IMAGE
        {image_data}
        ## USER REQUIREMENT
        {prompt}

        ---

        **IMPORTANT:**  
        Your output *must* be a complete, executable React application.  
        Do not generate explanations; focus solely on the code and structure as instructed.
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


