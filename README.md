1. Create a virtual environment by using the following commands
    i. uv init .
    ii. uv venv
    iii. uv pip install -r requirements.txt
2. Create file named .env, and add your groq api key like this.
    GROQ_API_KEY = "*************"
3. Run the mcp server using the command,
    uv run mcp-server.py
4. Run the flask server using the command,
    uv run agentic-system.py
5. For an example of the orchestration system,
    uv run agentic-example.py
   The agentic system in the code has the following format.
   <img width="441" height="249" alt="image" src="https://github.com/user-attachments/assets/a72cb99a-a0d4-4018-b7df-04badb58bb0c" />
