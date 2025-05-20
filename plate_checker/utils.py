"""
utils.py

This file contains utility functions for loading license plate data from files and saving results to CSV files.
"""

import os
import csv
from typing import List, Dict, Any
from .config import MIN_PLATE_LENGTH, MAX_PLATE_LENGTH


def load_plates_from_text(filepath: str) -> List[str]:
    """
    Load potential license plates from a text file.
    
    Args:
        filepath (str): Path to the text file containing potential plate values.
        
    Returns:
        List[str]: A sorted list of valid plate candidates filtered by length and sorted.
    """
    # If file exists, open it.
    if os.path.exists(filepath):
        # Load the modern word list.
        with open(filepath) as f:
            all_words = f.read().splitlines()

        # Filter words of length 2 to 7.
        test_list = [word.lower() for word in all_words if MIN_PLATE_LENGTH <= len(word) <= MAX_PLATE_LENGTH]
        
        # Sort by length (descending), then alphabetically.
        test_list = sorted(test_list, key=lambda word: (-len(word), word))

        print(f"\nTotal words found: {len(test_list)}\n")
        
        return test_list
        
    else:
        print("Failed to Find text file.")
        quit()


def save_to_file(results: Dict[str, str], save_file_path: str) -> None:
    """
    Save plate check results to a CSV file.
    
    Args:
        results (Dict[str, str]): Dictionary mapping plate numbers to their availability status.
        save_file_path (str): Path where the CSV file should be saved.
    
    Raises:
        IOError: If the file cannot be written.
    """
    # Ensure the file has a .csv extension.
    save_file_path = os.path.splitext(save_file_path)[0] + ".csv"

    output_dir = os.path.dirname(save_file_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except OSError as e:
            raise IOError(f"Failed to create output directory {output_dir}: {str(e)}")
    if os.path.exists(save_file_path) and not os.access(save_file_path, os.W_OK):
        raise IOError(f"No write permission for file: {save_file_path}")

    try:
        # Convert dictionary items to a list and sort by length (descending) then alphabetically.
        sorted_results = sorted(results.items(), key=lambda x: (-len(x[0]), x[0]))
        
        with open(save_file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Plate", "Status"])
            for plate, status in sorted_results:
                writer.writerow([plate, status])
    except IOError as e:
        raise IOError(f"Failed to write to file {save_file_path}: {str(e)}") 