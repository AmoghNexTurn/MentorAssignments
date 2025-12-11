import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "awaiting_feedback" not in st.session_state:
    st.session_state.awaiting_feedback = False
if "current_question" not in st.session_state:
    st.session_state.current_question = ""
if "faq_answer" not in st.session_state:
    st.session_state.faq_answer = ""

# Cache the model and embeddings initialization


@st.cache_resource
def load_models():
    model = ChatGroq(model="qwen/qwen3-32b", temperature=0,
                     reasoning_format="hidden")
    parser = StrOutputParser()
    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vs_faq = FAISS.load_local(
        "faiss_vs_faq",
        emb,
        allow_dangerous_deserialization=True,
    )

    vs_policies = FAISS.load_local(
        "faiss_vs_policies",
        emb,
        allow_dangerous_deserialization=True,
    )

    return model, parser, vs_faq, vs_policies


def format_faq(doc):
    pc = doc.page_content
    ans = pc.split("\"answer\": \"")[1].split("\"}")[0]
    return ans


# Load models
model, parser, vs_faq, vs_policies = load_models()

# Streamlit UI
st.title("💬 RAG Chatbot")
st.caption("Ask questions and get answers from FAQ or policy documents")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Ask a question..."):
    if not st.session_state.awaiting_feedback:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get FAQ answer
        with st.chat_message("assistant"):
            with st.spinner("Searching FAQ..."):
                top_faq = vs_faq.similarity_search(prompt, k=1)
                faq_answer = format_faq(top_faq[0])

                st.markdown(faq_answer)
                st.markdown("\n**Are you satisfied with this answer?**")

                # Store state for feedback handling
                st.session_state.awaiting_feedback = True
                st.session_state.current_question = prompt
                st.session_state.faq_answer = faq_answer
                st.session_state.messages.append(
                    {"role": "assistant", "content": faq_answer + "\n\n**Are you satisfied with this answer?**"})

# Feedback buttons
if st.session_state.awaiting_feedback:
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Yes", key="yes_btn", use_container_width=True):
            st.session_state.messages.append(
                {"role": "user", "content": "Yes"})
            st.session_state.messages.append(
                {"role": "assistant", "content": "Great! Feel free to ask another question."})
            st.session_state.awaiting_feedback = False
            st.session_state.current_question = ""
            st.session_state.faq_answer = ""
            st.rerun()

    with col2:
        if st.button("❌ No", key="no_btn", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "No"})

            # Search policies
            context = vs_policies.similarity_search(
                st.session_state.current_question, k=5)
            context_str = "\n\n".join(d.page_content for d in context)
            prompt_text = f"Answer ONLY from the provided context. If not found, say you don't know.\n\nQuestion: {st.session_state.current_question}\n\nContext:\n{context_str}"

            # Stream response
            full_response = ""
            stream = model.stream(prompt_text)
            for chunk in parser.transform(stream):
                full_response += chunk

            st.session_state.messages.append(
                {"role": "assistant", "content": full_response})

            st.session_state.awaiting_feedback = False
            st.session_state.current_question = ""
            st.session_state.faq_answer = ""
            st.rerun()

# Clear chat button in sidebar
with st.sidebar:
    st.header("Options")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.awaiting_feedback = False
        st.session_state.current_question = ""
        st.session_state.faq_answer = ""
        st.rerun()
