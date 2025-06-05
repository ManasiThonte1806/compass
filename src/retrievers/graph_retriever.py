# src/retrievers/graph_retriever.py

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j connection details
# Ensure these are set in your .env file or environment variables
# NEO4J_URI="bolt://localhost:7687"
# NEO4J_USERNAME="neo4j"
# NEO4J_PASSWORD="your_neo4j_password"

def get_graph_retriever():
    """
    Initializes and returns a function to execute Cypher queries against Neo4j.
    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "your_neo4j_password")

    print(f"Connecting to Neo4j at {uri}...")
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        print("Connected to Neo4j successfully.")

        def retrieve_graph_data(cypher_query: str):
            """
            Executes a Cypher query against the Neo4j database.
            Args:
                cypher_query (str): The Cypher query string.
            Returns:
                list: A list of dictionaries, where each dictionary represents a record
                      returned by the Cypher query.
            """
            # Ensure the query is stripped of any leading/trailing whitespace or hidden chars
            cleaned_cypher_query = cypher_query.strip()
            # AND ALSO remove any backticks (`) that might still be present
            cleaned_cypher_query = cleaned_cypher_query.replace("`", "") # NEW: Remove backticks
            print(f"Executing Cypher query:\n{cleaned_cypher_query}")
            with driver.session() as session:
                result = session.run(cleaned_cypher_query)
                records = [record.data() for record in result]
            print(f"Found {len(records)} records.")
            return records

        print("Graph retriever initialized successfully.")
        return retrieve_graph_data

    except Exception as e:
        print(f"Error connecting to Neo4j or initializing graph retriever: {e}")
        print("Please ensure Neo4J is running and NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD are correctly set in your .env file.")
        return None

if __name__ == "__main__":
    # Example usage:
    # IMPORTANT: Before running this, ensure Neo4j is running and you've created
    # the sample data using the Cypher queries provided in Task 1.
    # Also, set your NEO4J_PASSWORD in your .env file.

    # Install neo4j driver: pip install neo4j

    graph_retriever = get_graph_retriever()
    if graph_retriever:
        print("\n--- Testing Graph Retriever ---")

        # Query 1: Find all persons and their roles
        query_1 = "MATCH (p:Person) RETURN p.name AS Name, p.role AS Role LIMIT 5"
        results_1 = graph_retriever(query_1)
        print("\nPersons and Roles:")
        for res in results_1:
            print(f"  - Name: {res.get('Name')}, Role: {res.get('Role')}")

        # Query 2: Find who manages whom
        query_2 = "MATCH (manager:Person)-[:MANAGES]->(employee:Person) RETURN manager.name AS Manager, employee.name AS Employee"
        results_2 = graph_retriever(query_2)
        print("\nManagement Relationships:")
        for res in results_2:
            print(f"  - {res.get('Manager')} manages {res.get('Employee')}")

        # Query 3: Find projects a person works on
        query_3 = "MATCH (p:Person {name: 'Bob Johnson'})-[:WORKS_ON]->(proj:Project) RETURN proj.name AS ProjectName"
        results_3 = graph_retriever(query_3)
        print("\nProjects Bob Johnson works on:")
        for res in results_3:
            print(f"  - {res.get('ProjectName')}")

    else:
        print("Graph retriever could not be initialized. Cannot run example queries.")
