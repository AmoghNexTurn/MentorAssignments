1. Create a virtual environment by using the following commands i. uv init . ii. uv venv iii. uv pip install -r requirements.txt
3. Create a .env file and in the .env file, fill in your groq api key.
4. Run the generate_embeddings.py file using the command, uv run generate_embeddings.py. This generates two folders faiss_vs_faq and faiss_vs_policies.
5. For the chat application, run rag_streamlit.py using the command, streamlit run rag_streamlit.py.
6. Open localhost:8501 in your browser.