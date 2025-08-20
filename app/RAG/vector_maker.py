import os
from langchain.text_splitter import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import UnstructuredFileLoader
import logging
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()
# Create embedding instance using Ollama
embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")

current_dir = os.path.dirname(os.path.abspath(__file__))
extracted_data_dir = os.path.join(current_dir, "..", "docs_scrapers", "extracted_data")
file_paths = glob.glob(os.path.join(extracted_data_dir,"*.txt"))
print(file_paths)
# Create path for storing the vector database
message=""
persistent_directory = os.path.join(current_dir, "db", "chroma_db")
def vector_maker():
    logger.info("Calling vector_maker function")
    if not os.path.exists(persistent_directory):
        logger.info("Persistent directory does not exist. Creating it...")
        # Create the directory and its parents
        os.makedirs(persistent_directory, exist_ok=True)
        if not os.path.exists(extracted_data_dir):
            raise FileNotFoundError(
                f"The file {extracted_data_dir} does not exist. Please check the path."
            )
        if len(file_paths)==0 or len(file_paths)!=7:
            raise ValueError(
                f"Expected 5 text files, but found {len(file_paths)}. Please create the missing files."
            )
        all_documents=[]
        # Load the text file
        meta_data_docs_name=[]
        for file in file_paths:
            logger.info(f"Loading file: {file}")
            # Create an UnstructuredFileLoader for the file and load its contents.
            loader= UnstructuredFileLoader(file)
            docs=loader.load()
            for doc in docs:
                logger.info("Setting metadata for the document")
                file_name= os.path.basename(file)
                name_only=file_name.rsplit(".",1)[0]
                name_parts=name_only.split("_")
                doc.metadata["source"]=name_parts[1]
                logger.info("**Metadata set for the document**")
                logger.info(f"Metadata source: {doc.metadata['source']}")
                meta_data_docs_name.append(name_parts[1])

            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            split_docs = text_splitter.split_documents(docs)
            all_documents.extend(split_docs)
        # Create the vector store
        logger.info("Creating vector store")
        db = Chroma.from_documents(
            documents=all_documents,
            embedding=embeddings,
            persist_directory=persistent_directory
        )
        logger.info(f"Vector store created and saved to {persistent_directory}")
        message="Vector store created and saved"
        for i in meta_data_docs_name:
            logger.info(f"Document source: {i}")
        return message
    else:
        message="Persistent directory already exists."
        return message
