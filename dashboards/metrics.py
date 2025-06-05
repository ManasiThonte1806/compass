# dashboards/metrics.py

import pandas as pd
import streamlit as st
import datetime
import os
import logging
import json # NEW: Import json

def load_logs(log_file: str = "ui/agent_calls.log") -> pd.DataFrame: # Corrected path
    """
    Loads agent call logs from a JSONL file into a pandas DataFrame.

    Args:
        log_file (str, optional): The name of the log file. Defaults to "ui/agent_calls.log".

    Returns:
        pd.DataFrame: A DataFrame containing the log data.
                      Returns an empty DataFrame if the file doesn't exist or is empty.
    """
    # Ensure log_file path is absolute if running from different directories
    script_dir = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(script_dir, '..')) # Go up to allyin-compass
    log_file_path = os.path.join(project_root, log_file) # Construct full path

    if not os.path.exists(log_file_path) or os.path.getsize(log_file_path) == 0:
        logging.warning(f"Log file '{log_file_path}' not found or is empty. Returning empty DataFrame.")
        return pd.DataFrame()

    data = []
    try:
        with open(log_file_path, "r") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    data.append(record)
                except json.JSONDecodeError:
                    logging.error(f"Skipping invalid JSON line in log file: {line.strip()}")
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        logging.error(f"An error occurred while loading logs from {log_file_path}: {e}")
        return pd.DataFrame()

def calculate_queries_per_day(df: pd.DataFrame) -> pd.Series:
    """
    Calculates the number of queries per day from the log data.
    """
    if df.empty:
        return pd.Series()
    df['date'] = df['timestamp'].dt.date
    return df.groupby('date').size()

def calculate_tool_usage(df: pd.DataFrame) -> pd.Series:
    if df.empty or 'tool_usage' not in df.columns:
        return pd.Series()

    tool_counts = {}
    for usage_dict in df['tool_usage'].dropna():
        for tool_name, count in usage_dict.items():
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + count

    tool_series = pd.Series(tool_counts)
    return tool_series.sort_values(ascending=False)


def calculate_avg_response_time(df: pd.DataFrame) -> float:
    """
    Calculates the average response time for the agent.
    """
    if df.empty or 'response_time' not in df.columns:
        return 0.0
    return df['response_time'].mean()

