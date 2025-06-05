# feedback/logger.py

import json
import os
from datetime import datetime

def log_feedback(query: str, answer: str, rating: int, log_file: str = "feedback_log.jsonl"):
    """
    Logs user feedback to a JSONL file.

    Args:
        query (str): The user's query.
        answer (str): The agent's answer.
        rating (int): The user's rating (e.g., 1 for thumbs up, -1 for thumbs down).
        log_file (str, optional): The name of the log file. Defaults to "feedback_log.jsonl".
    """
    feedback_data = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "answer": answer,
        "rating": rating
    }

    # Ensure the directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(feedback_data) + "\n")
        print(f"Feedback logged to {log_file}")
    except Exception as e:
        print(f"Error logging feedback: {e}")

if __name__ == "__main__":
    # Example Usage (for testing)
    log_feedback("What is the capital of France?", "The capital of France is Paris.", 1)
    log_feedback("What is the meaning of life?", "42", -1)