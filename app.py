import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

# Load environment variables
load_dotenv()

# Initialize API client
api_key = os.getenv("llm_api_key")
client = OpenAI(
    api_key=api_key,
    base_url="https://openai.rc.asu.edu/v1"
)

# Initialize ChromaDB
@st.cache_resource
def get_chroma_collection():
    try:
        chroma_client = chromadb.PersistentClient(path="data/chroma_db")
        return chroma_client.get_collection(name="linkedin_posts")
    except Exception as e:
        st.error(f"Failed to connect to ChromaDB: {e}")
        return None

collection = get_chroma_collection()

def get_rag_response(user_query):
    if not collection:
        return "ChromaDB connection is not available."
    
    try:
        sources = ["LinkedIn", "TechCrunch", "JobBoards", "StartupGallery"]
        all_documents = []
        all_metadatas = []
        
        for source in sources:
            try:
                results = collection.query(
                    query_texts=[user_query],
                    n_results=3,
                    where={"source": source}
                )
                if results['documents'] and results['documents'][0]:
                    all_documents.extend(results['documents'][0])
                    all_metadatas.extend(results['metadatas'][0] if 'metadatas' in results and results['metadatas'] else [{}] * len(results['documents'][0]))
            except Exception as e:
                print(f"Warning: Failed to retrieve from source {source}: {e}")
                continue
        
        if not all_documents:
            return "No relevant context found in the database."
        
        # Construct context string
        context_parts = []
        for doc, meta in zip(all_documents, all_metadatas):
            context_str = (
                f"---\nPlatform: {meta.get('source', 'Unknown')}\n"
                f"Author/Entity: {meta.get('author_name', 'Unknown')}\n"
                f"URL: {meta.get('post_url', 'Unknown')}\n"
            )
            # Add granular metadata
            for key, value in meta.items():
                if key not in ['source', 'author_name', 'post_url', 'source_topic'] and value:
                    context_str += f"{key.replace('_', ' ').title()}: {value}\n"
            
            context_str += f"Content: {doc}\n"
            context_parts.append(context_str)
        
        context_string = "\n".join(context_parts)
        
        # Send to ASU LLM
        system_prompt = (
            "You are TrendScout AI, an elite market intelligence analyst. You are provided with market intelligence from multiple distinct sources (e.g., LinkedIn sentiment, TechCrunch funding news, Job Board data). Your job is to synthesize this data into overarching market trends and strategic insights.\n"
            "SYNTHESIS RULES:\n\n"
            "Cross-Reference: Always attempt to connect sentiment (e.g., LinkedIn) with tangible market movements (e.g., Funding/Jobs) if the data is available.\n\n"
            "Highlight Nuance: If sources agree, state the consensus. If they conflict, you MUST highlight the discrepancy. Do not lean on just one source.\n"
            "CITATION RULES (CRITICAL):\n\n"
            "MANDATORY CITATION FOR SUMMARIES: You must include an inline citation formatted as [Platform - Author Name](URL) for every single claim, trend, or summary you generate. Even if you are heavily paraphrasing or combining multiple ideas, you must cite the sources that led you to that conclusion.\n\n"
            "MULTI-CITATION: If a synthesized trend comes from multiple sources, cite all of them at the end of the sentence or paragraph (e.g., 'The market is shifting towards Edge AI [LinkedIn - Jane Doe](url) [TechCrunch - John Smith](url)').\n\n"
            "NO ORPHANED CLAIMS: Do not output any factual statement, sentiment analysis, or trend without attaching its source link."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context_string}\n\nQuery:\n{user_query}"}
        ]
        
        response = client.chat.completions.create(
            model="qwen3-235b-a22b-instruct-2507",
            messages=messages
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"An error occurred while generating the response: {str(e)}"

# Streamlit UI
st.title("TrendScout AI")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask about LinkedIn trends..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get response and display
    with st.chat_message("assistant"):
        with st.spinner("Analyzing LinkedIn data..."):
            response = get_rag_response(prompt)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
