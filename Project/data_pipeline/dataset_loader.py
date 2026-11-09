"""Reads tables from disk and writes them back.

This is the only module of the data preparation section that touches CSV files.
"""

import os

import pandas as pd


def load_raw_dataset(file_path, null_tokens):
    """Read one raw extract with every column as text and every missing token empty."""
    return pd.read_csv(file_path, dtype=str, keep_default_na=True,
                       na_values=list(null_tokens), low_memory=False)


def load_processed_dataset(file_path):
    """Read a cleaned table, or the live queue, letting the file's contents set the types."""
    return pd.read_csv(file_path, low_memory=False)


def save_processed_dataset(dataframe, file_path):
    """Write a cleaned table without an index column, creating its folder if needed."""
    folder = os.path.dirname(file_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    dataframe.to_csv(file_path, index=False)
    return file_path
