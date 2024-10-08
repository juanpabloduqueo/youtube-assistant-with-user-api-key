import openai
from langchain_community.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
import streamlit as st
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize OpenAI embeddings
def initialize_embeddings(api_key: str) -> OpenAIEmbeddings:
    return OpenAIEmbeddings(openai_api_key=api_key)

video_url = "https://youtu.be/-Osca2Zax4Y?si=RE045YHRPMfA7oR5"

def create_vector_from_youtube_url(video_url: str, language: str, api_key: str) -> FAISS:
    """
    Creates a vector representation of the given YouTube video URL.
    Parameters:
        video_url (str): The URL of the YouTube video.
    Returns:
        FAISS: The vector representation of the YouTube video.
    Raises:
        <Any exceptions that may be raised>
    Example:
        video_url = "https://www.youtube.com/watch?v=abc123"
        vector = create_vector_from_youtube_url(video_url)
    """
    try:
        logging.info(f"Fetching transcript for video URL: {video_url} in language: {language}")
        loader = YoutubeLoader.from_youtube_url(video_url, language=language)
        transcript = loader.load()
        
        if not transcript:
            logging.error("Transcript is empty. Check the input video URL and language.")
            raise ValueError("Transcript is empty. Check the input video URL and language.")
        
        logging.info(f"Transcript fetched: {transcript}")
               
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = text_splitter.split_documents(transcript)
        
        if not docs:
            logging.error("No documents were generated. Check the input video URL and language.")
            raise ValueError("No documents were generated. Check the input video URL and language.")

        embeddings = initialize_embeddings(api_key)
        embeddings_list = embeddings.embed_documents([doc.page_content for doc in docs])
        
        if not embeddings_list:
            logging.error("No embeddings were generated. Check the input documents and embedding model.")
            raise ValueError("No embeddings were generated. Check the input documents and embedding model.")
             
        db = FAISS.from_documents(docs, embeddings)
        return db
    
    except Exception as e:
        logging.error(f"Error creating vector from YouTube URL: {e}")
        raise ValueError(f"Error creating vector from YouTube URL: {e}")

def get_response_from_query(db, query, language, api_key,k=4):
    """
    Retrieves a response to a query based on a similarity search in a database.
    Parameters:
    - db (Database): The database object used for similarity search.
    - query (str): The query string.
    - k (int): The number of documents to retrieve (default is 4).
    Returns:
    - response (str): The response generated by the YouTube assistant.
    - docs (list): The list of documents retrieved from the database.
    Raises:
    - None
    Example usage:
    response, docs = get_response_from_query(db, "How to cook pasta?")
    """

    docs = db.similarity_search(query, k=k)
    docs_page_content = " ".join([doc.page_content for doc in docs])
    
    llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18", openai_api_key=api_key)
    
    language_str = 'Spanish' if language == 'es' else 'German' if language == 'de' else 'English'
    
    prompt_template = PromptTemplate(
        input_variables=["question", "docs", "language"],
        template="""You are a helpful YouTube assistant that can answer questions about videos based on
        the video transcript. 
        
        Answer the following question: {question}
        By searching the following video transcript: {docs}
        
        Only use the factual information from the vide transcript to answer the question.
        If you feel like you don't have enough information to answer the question, say "I don't know".
        Your answer should be detailed.
        
        Provide the answer only in {language}.
        
        Use markdown format for the anwser. Use new lines as appropriate, especially when enumerating different 
        points or steps.        
        """)
    # runnable sequence
    runnable_sequence = prompt_template | llm 
    
    # Run the LLMchain
    response = runnable_sequence.invoke({'question': query, 'docs': docs_page_content, 'language': language_str})
    response = response.content.replace("\n", "")
    return response, docs