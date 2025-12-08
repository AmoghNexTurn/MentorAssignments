import streamlit as st
import requests
import json

st.set_page_config(page_title="Agent API Frontend", layout="wide")

st.title("🤖 Agent API Interface")
st.markdown("Interact with indexed_agent and non_indexed_agent via simple UI.")

# Sidebar for configuration
st.sidebar.header("API Configuration")
api_base = st.sidebar.text_input(
    "API Base URL", value="http://localhost:8001", help="Base URL of your FastAPI server")
agent_options = ["indexed_agent", "non_indexed_agent"]

with st.expander("📋 Sample Queries", expanded=False):
    st.markdown("""
    ```
    Get me the data for user_id 838719 from the database
    Show data for category 50
    Get me the data from database where user_id is 838719 and category is 20
    ```
    """)

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []


# Agent selector
col1, col2 = st.columns([3, 1])
with col1:
    selected_agent = st.selectbox(
        "Select Agent", agent_options, key="agent_select")
with col2:
    test_mode = st.checkbox("Test Mode", help="Use predefined test query")

# Input
if prompt := st.chat_input("Enter your query (e.g., 'Get me the data for user_id 838719 from the indexed database')"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare request
    with st.chat_message("assistant"):
        with st.spinner("Calling agent..."):
            url = f"{api_base}/agent/{selected_agent}"
            payload = {
                "messages": [{"role": "user", "content": prompt}]
            }

            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json",
                             "Accept": "application/json"},
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    st.markdown(result)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": result})
                elif response.status_code == 404:
                    error_msg = response.json().get("message", "Agent not found")
                    st.error(f"❌ {error_msg}")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"Error: {error_msg}"})
                else:
                    st.error(f"❌ HTTP {response.status_code}: {response.text}")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"HTTP Error {response.status_code}"})

            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection failed: {str(e)}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"Connection Error: {str(e)}"})

# Test button
if st.button("🧪 Run Test Query", type="secondary"):
    test_query = "Get me the data for user_id 838719 from the database"
    st.session_state.messages.append({"role": "user", "content": test_query})
    with st.chat_message("user"):
        st.markdown(test_query)

    with st.chat_message("assistant"):
        with st.spinner("Running test query..."):
            url = f"{api_base}/agent/{selected_agent}"
            payload = {
                "messages": [{"role": "user", "content": test_query}]
            }

            try:
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ Test successful!")
                    st.markdown(result)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": result})
                else:
                    st.error(f"❌ Test failed: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Test connection failed: {str(e)}")

# Clear chat
if st.sidebar.button("🗑️ Clear Chat", type="secondary"):
    st.session_state.messages = []
    st.rerun()
