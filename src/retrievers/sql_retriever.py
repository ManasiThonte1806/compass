# src/retrievers/sql_retriever.py

import os
import duckdb
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain.agents import AgentType

load_dotenv() # Loads variables from .env into environment

def get_sql_agent():
    """
    Initializes and returns a LangChain SQL agent connected to DuckDB.
    This agent can understand natural language questions and convert them
    into SQL queries to fetch data from the DuckDB database, using Google Gemini.
    """
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    data_path = os.path.join(project_root, 'data', 'structured')
    db_path = os.path.join(data_path, 'allyin_compass.db')

    print(f"Connecting to DuckDB for SQL retrieval at: {db_path}")
    try:
        # Create a SQLAlchemy engine from the DuckDB connection string
        engine = create_engine(f"duckdb:///{db_path}")
        db = SQLDatabase(engine)

        # Initialize the LLM with Google Gemini 1.5 Flash
        # Changed model from "gemini-pro" to "gemini-1.5-flash" for better availability
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

        # Create the SQL agent with a more generic agent type
        agent_executor = create_sql_agent(
            llm=llm,
            db=db,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            # Removed handle_parsing_errors=True as it's no longer supported
        )
        print("SQL agent initialized successfully using Google Gemini.")
        return agent_executor
    except Exception as e:
        print(f"Error initializing SQL agent: {e}")
        print("Please ensure DuckDB file exists and GOOGLE_API_KEY is configured in your .env file.")
        print(f"Detailed error: {e}")
        return None

if __name__ == "__main__":
    sql_agent = get_sql_agent()
    if sql_agent:
        print("\n--- Testing SQL Agent ---")
        try:
            print("\nQuery: How many customers are there?")
            response = sql_agent.invoke({"input": "How many customers are there?"})
            print(f"Response: {response['output']}")

            print("\nQuery: What are the names and prices of products in the Electronics category?")
            response = sql_agent.invoke({"input": "What are the names and prices of products in the Electronics category?"})
            print(f"Response: {response['output']}")

            print("\nQuery: Show me the total quantity ordered for each product.")
            response = sql_agent.invoke({"input": "Show me the total quantity ordered for each product."})
            print(f"Response: {response['output']}")

        except Exception as e:
            print(f"An error occurred during SQL agent query: {e}")
            print(f"Detailed query error: {e}")
    else:
        print("SQL agent could not be initialized. Cannot run example queries.")
