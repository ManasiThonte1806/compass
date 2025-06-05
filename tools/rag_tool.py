import os
import re
import json
import logging
from typing import Union, Dict, List
from langchain_core.prompts import PromptTemplate
from src.retrievers.vector_retriever import get_vector_retriever

def _load_doc_by_filename(filename: str) -> List[Dict]:
    parsed_path = os.path.join("data", "unstructured", "parsed.jsonl")
    docs = []
    try:
        with open(parsed_path, "r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                if doc.get("filename", "").lower() == filename.lower():
                    logging.info(f"[RAG Tool] Found matching doc for: {filename}")
                    docs.append(doc)
                    break
    except Exception as e:
        logging.error(f"[RAG Tool] Could not load {filename} from parsed.jsonl: {e}")
    return docs

def create_rag_tool(llm):
    if llm is None:
        raise ValueError("LLM instance cannot be None when creating RAG tool.")

    prompt_template = """
    You are a helpful AI assistant. Use the information provided from the document "{filename}" to answer the user's question.
    Cite the filename in your response. If the answer is not in the document, say so clearly.

    User Question:
    {query}

    Context:
    {context}
    """
    prompt = PromptTemplate.from_template(prompt_template)

    def rag_tool(payload: Union[str, Dict]) -> str:
        """
        Accepts either:
        • A dict  -> {"query": "<question>", "filename": "<file.pdf|file.eml>"}
        • A str   -> plain question text (we will try to regex-extract the filename)
        """

        # 1️⃣ Normalize inputs
        if isinstance(payload, dict):
            query = payload.get("query", "").strip()
            filename = payload.get("filename", "").strip()
        elif isinstance(payload, str):
            query = payload.strip()
            m = re.search(r"[A-Za-z0-9_.-]+\.(?:pdf|eml)", query)
            filename = m.group(0) if m else ""
        else:
            return "Error: Unsupported input type for RAG tool."

        if not filename:
            return "Error: No filename provided or detected for RAG tool."

        # 2️⃣ Load document by filename
        docs = _load_doc_by_filename(filename)
        if not docs:
            return f"Error: Document '{filename}' not found in parsed.jsonl."

        # 3️⃣ Build context
        context = ""
        for doc in docs:
            doc_type = doc.get("type", "").lower()
            if doc_type == "email":
                content = f"Subject: {doc.get('subject', '')}\n{doc.get('body', '')}"
            else:
                content = doc.get("content", "")
            context += f"Filename: {filename}\n{content}\n\n"

        # 4️⃣ Generate answer with LLM
        formatted_prompt = prompt.format(query=query, context=context, filename=filename)
        try:
            answer = llm.invoke(formatted_prompt).content

            # 5️⃣ Select a real sentence from context for "Source:"
            sentences = re.split(r'(?<=[.!?]) +', context.strip())
            best_sentence = next((s for s in sentences if len(s.split()) > 5), "No matching sentence found.")

            return f"{answer}\n\nSource: {best_sentence}"
        except Exception as e:
            logging.error(f"[RAG Tool] LLM error: {e}")
            return "Error: Failed to generate an answer from the document."

    return rag_tool
