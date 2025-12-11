import os
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, RecursiveJsonSplitter
import json
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq  # Groq LangChain integration

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableParallel,
    RunnablePassthrough,
    RunnableLambda,
)
from langchain_core.output_parsers import StrOutputParser

load_dotenv()
emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

TXT_PATH = "policies.txt"  # <-- change to your TXT filename

# 1) Load TXT
loader = TextLoader(TXT_PATH, encoding="utf-8")
text_docs = loader.load()  # one Document with full text

# 2) Chunk
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=150)
splits = text_splitter.split_documents(text_docs)

# 3) Embed + index (SentenceTransformers)

vs_policies = FAISS.from_documents(splits, emb)

with open("faq.json", "r") as f:
    json_data = json.load(f)

json_splitter = RecursiveJsonSplitter(max_chunk_size=300)
docs = json_splitter.create_documents(texts=[json_data], convert_lists=True)
vs_faq = FAISS.from_documents(docs, emb)

vs_policies.save_local("faiss_vs_policies")
vs_faq.save_local("faiss_vs_faq")
