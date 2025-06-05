# **AllyIn Compass: Discovery & Intelligence Engine**

## **Overview**

AllyIn Compass is your smart enterprise assistant, designed to revolutionize how you interact with your company's data. In today's fast-paced business environment, organizations grapple with vast amounts of disparate information  from structured spreadsheets to complex documents and interconnected graphs. This often leads to missed insights and inefficient decision-making. AllyIn Compass addresses this challenge by providing a unified platform that can answer complex questions by intelligently navigating and synthesizing information across these diverse data sources.

Leveraging cutting-edge AI technologies like Retrieval-Augmented Generation (RAG) and intelligent agents, AllyIn Compass aims to act as a central intelligence hub, enabling users to quickly discover critical insights and make informed decisions.

## **Key Features**

* **Intelligent Agent-based Query Handling:** Powered by LangChain, the system's core agent dynamically chooses the most appropriate tools (SQL, Vector, Graph, RAG) to answer complex queries.  
* **Retrieval-Augmented Generation (RAG):** Combines information retrieval with powerful Large Language Models (LLMs) to generate coherent, context-aware, and cited answers.  
* **Multi-modal Data Integration:** Seamlessly searches across:  
  * **Structured Data:** Spreadsheets and tabular data loaded into DuckDB.  
  * **Unstructured Data:** PDFs and emails parsed and vectorized in Qdrant.  
  * **Graph Data:** Relationships stored in Neo4j.  
* **PII Filtering & Compliance Guardrails:** Automatically detects and redacts sensitive Personal Identifiable Information (PII) and flags content related to compliance concerns.  
* **Interactive User Interface (UI):** Built with Streamlit, providing an intuitive experience for asking questions, filtering results, and viewing answers.  
* **Observability Dashboard:** Tracks key metrics like query volume and tool usage frequency for system monitoring and improvement.  
* **Feedback Loop:** Allows users to provide feedback (thumbs up/down) on answers to continuously improve model performance through fine-tuning simulations.  
* **Source Text Highlighting:** Highlights the specific source text in the answer window for transparency and credibility.

## **Setup Instructions**

Follow these steps to get AllyIn Compass up and running on your local machine.

### **Prerequisites**

* **Docker Desktop:** Essential for running Qdrant and Neo4j databases.  
* **Python 3.10+:** The primary programming language for the project.  
* **Git:** For cloning the repository.  
* **VS Code:** Recommended Integrated Development Environment (IDE).  
* **Postman:** Useful for testing APIs, if applicable.  
* **OpenAI API Key:** Required for the Large Language Model (LLM)   functionality. Set this as an environment variable (e.g., OPENAI\_API\_KEY).

### **Cloning the Repository**

Bash

git clone https://github.com/your-username/allyin-compass.git  
cd allyin-compass

### **Python Environment Setup**

1. **Create a virtual environment:**  
2. Bash: python \-m venv venv  
3. **Activate the virtual environment:**  
   * On macOS/Linux:  
   * Bash: source venv/bin/activate  
   * On Windows:  
   * Bash: .\\venv\\Scripts\\activate  
4. **Install dependencies:**  
5. Code snippet: pip install \-r requirements.txt

### **Database Setup (using Docker)**

1. **Start Qdrant (Vector Database):**  
2. Bash: docker run \-p 6333:6333 qdrant/qdrant  
3. *Verify Qdrant is running by checking localhost:6333.*  
4. **Start Neo4j (Graph Database):**  
5. Bash: docker run \-p 7687:7687 \-p 7474:7474 \--env NEO4J\_AUTH=neo4j/password neo4j  
6. *You can access Neo4j Browser at localhost:7474 with username neo4j and password password.*

### **Data Ingestion**

Before running queries, you need to ingest sample data into your databases.

**Prepare Data Folders:**

Bash: mkdir \-p data/structured, mkdir \-p data/unstructured

**Add Sample Data:**

* Place sample CSV files (customers.csv, orders.csv, emissions.csv) into data/structured/.  
  * Collect 3 PDF files and 3 .eml (email) files and place them into data/unstructured/.

  **Run Ingestion Scripts (from project root with virtual environment activated):**

  Bash

\# For structured data (DuckDB)  
python src/ingest/structured\_loader.py

\# For unstructured data (parsing and saving as JSONL)  
python src/ingest/document\_parser.py

\# For embedding unstructured data into Qdrant  
python src/ingest/embedder.py

\# For graph data   
\# python src/ingest/graph\_loader.py   
\# Manually create 10 entities and their connections in Neo4j Desktop/Sandbox 

## **How to Run a Query**

1. **Start the Streamlit UI:**  
2. Bash: streamlit run ui/app.py  
3. This will open the AllyIn Compass UI in your web browser, typically at http://localhost:8501.  
4. **Interact with the UI:**

   * Enter your question in the "Ask a question" text box.  
   * Select the relevant "Domain" (e.g., General, Finance, Biotech, Energy).  
   * Use the "Select Source" dropdown to filter by specific files like pdf1.pdf or emaill.eml as needed.  
   * Click the "Get Answer" button.

## **Credits**

**Project Lead:** Manasi Thonte

**Core Technologies Used:**

* **LangChain:** For agent orchestration and tool chaining.  
* **Streamlit:** For building the interactive user interface.  
* **OpenAI:** For the Large Language Model capabilities (GPT-4).  
* **Qdrant:** As the high-performance vector database.  
* **DuckDB:** For efficient in-process SQL database operations.  
* **Neo4j:** For managing graph data and relationships.  
* **Pandas:** For data manipulation.  
* **PyMuPDF (fitz):** For PDF text extraction.  
* **Python** email **package:** For email parsing.  
* **Sentence-Transformers:** For generating text embeddings.  
* **Hugging Face (PEFT \+ LoRA):** For fine-tuning simulations.

