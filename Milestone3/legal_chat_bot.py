import os
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.schema import AIMessage, HumanMessage
from chatbot_system_template import SYSTEM_TEMPLATE
from config import GOOGLE_API_KEY, OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["USE_TF"] = "0"

# -------------------- Set environment variables --------------------
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["PINECONE_ENVIRONMENT"] = PINECONE_ENVIRONMENT
os.environ["PINECONE_INDEX_NAME"] = PINECONE_INDEX_NAME

if GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

INDEX_NAME = PINECONE_INDEX_NAME


def _build_llm():
    """Build LLM — prefers Google Gemini, falls back to OpenAI."""
    if GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            print("Using Google Gemini (gemini-3.8-flash) as LLM")
            return ChatGoogleGenerativeAI(
                model="gemini-3.8-flash",
                temperature=0.3,
                google_api_key=GOOGLE_API_KEY,
            )
        except Exception as e:
            print(f"Gemini init failed ({e}), falling back to OpenAI...")

    from langchain_openai import ChatOpenAI
    print("Using OpenAI gpt-4o-mini as LLM")
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=OPENAI_API_KEY)


# -------------------- RAG Chain Creation --------------------
def create_rag_chain():
    print("Loading RAG chain resources...")

    # Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )

    # LLM (Gemini preferred, OpenAI fallback)
    llm = _build_llm()

    # Pinecone vectorstore
    try:
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=INDEX_NAME,
            embedding=embeddings
        )
    except ValueError as e:
        raise ValueError(
            f"Error connecting to Pinecone: {e}. "
            "Make sure your PINECONE_API_KEY, PINECONE_ENVIRONMENT, and PINECONE_INDEX_NAME are correct."
        )

    print("Connected to Pinecone vectorstore")

    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    print("Retriever created")

    # Prompt template
    final_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE + "\n\nUse the following retrieved context:\n{context}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}")
    ])

    # Chain
    question_answer_chain = create_stuff_documents_chain(llm, final_prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    print("RAG chain loaded successfully")
    return rag_chain


# -------------------- Query Function --------------------
def ask_query(rag_chain, user_query, chat_history):
    # Convert Streamlit chat_history to LangChain messages
    formatted_history = []
    for msg in chat_history:
        if msg["role"] == "user":
            formatted_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            formatted_history.append(AIMessage(content=msg["content"]))

    try:
        response = rag_chain.invoke({
            "input": user_query,
            "chat_history": formatted_history
        })
        return response["answer"]
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "invalid_api_key" in err_str or "AuthenticationError" in type(e).__name__:
            return (
                "⚠️ **Authentication Error**: The configured API key is invalid or expired.\n\n"
                "Please update `GOOGLE_API_KEY` or `OPENAI_API_KEY` in `Milestone3/.env`."
            )
        elif "rate_limit" in err_str.lower() or "quota" in err_str.lower() or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            return (
                "⚠️ **API Quota Exceeded**: The AI service quota has been exceeded.\n\n"
                "- For Google Gemini: check https://aistudio.google.com/\n"
                "- For OpenAI: check https://platform.openai.com/account/billing"
            )
        else:
            return f"⚠️ **Error executing query**: {err_str}"
