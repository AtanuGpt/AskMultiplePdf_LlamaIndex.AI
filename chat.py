import os
import faiss
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.vector_stores.faiss import FaissVectorStore

d = 1536
faiss_index = faiss.IndexFlatL2(d)
PERSIST_DIR = "./storage"

def saveUploadedFiles(pdf_docs):
    UPLOAD_DIR = 'uploaded_files'
    try:
        for pdf in pdf_docs:
            file_path = os.path.join(UPLOAD_DIR, pdf.name)
            with open(file_path, "wb") as f:
                f.write(pdf.getbuffer())
        return "Done"
    except:
        return "Error"

def doVectorization():    
    try:
        vector_store = FaissVectorStore(faiss_index=faiss_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store) 
        documents = SimpleDirectoryReader("./uploaded_files").load_data()
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context
        )
        index.storage_context.persist()
        return "Done"
    except:
        return "Error"

def fetchData(user_question):
    try:
        vector_store = FaissVectorStore.from_persist_dir("./storage")
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store, persist_dir=PERSIST_DIR
        )
        index = load_index_from_storage(storage_context=storage_context)
        query_engine = index.as_query_engine()
        response = query_engine.query(user_question)
        return str(response)
    except:
        return "Error"

#============================================================================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello, I am a bot. How can I help you?")
    ]

def main():
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

    st.set_page_config(
        page_title="Chat with multiple PDFs",
        page_icon=":sparkles:"
    )

    st.header("Chat with single or multiple PDFs :sparkles:")

    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
               st.markdown(message.content)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", 
            accept_multiple_files=True
        )

        if st.button("Process"):
            with st.spinner("Processing"):
                IsFilesSaved = saveUploadedFiles(pdf_docs)
                if IsFilesSaved == "Done":
                    IsVectorized = doVectorization()
                    if IsVectorized == "Done":
                        st.session_state.isPdfProcessed = "done"
                        st.success("Done!")
                    else:
                        st.error("Error! in vectorization")
                else:
                    st.error("Error! in saving the files")

    
    if "isPdfProcessed" in st.session_state:
        user_question = st.chat_input("Ask a question about your document(s):")

        if user_question is not None and user_question != "":
            st.session_state.chat_history.append(HumanMessage(content=user_question))

            with st.chat_message("Human"):
                st.markdown(user_question)
            
            with st.chat_message("AI"):
                with st.spinner("Fetching data ..."):
                    response = fetchData(user_question)
                    st.markdown(response)    
            
            st.session_state.chat_history.append(AIMessage(content=response))

#============================================================================================================
if __name__ == '__main__':
    main()