1. Create a virtual environment by using the following commands i. uv init . ii. uv venv iii. uv pip install -r requirements.txt
2. Then in the database directory, run docker compose up -d
3. In the .env file, fill in your api keys.
4. Run the database API server using the command, uvicorn db-api:app --reload
5. Run the flask server using the command, uvicorn agentic-api:app --port 8001 --reload
6. Run the frontend file using streamlit run frontend.py

<img width="710" height="549" alt="Screenshot From 2025-12-02 11-41-33" src="https://github.com/user-attachments/assets/7c6b458e-1d62-494f-92f9-ac407ecbae72" />
