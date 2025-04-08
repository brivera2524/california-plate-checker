"""
plate_checker.py

This file provides functionality to check the availability of license plates
with the California DMV. It handles concurrent processing of multiple plate checks
using asynchronous workers.
"""

import asyncio
import aiohttp
from colorama import Fore, Style
import os
import csv
from typing import List, Dict, Any, Optional
import argparse
from time import time
import shutil
from openai import AsyncOpenAI  # Import AsyncOpenAI for async compatibility
from dotenv import load_dotenv  # Import to load .env file

from config import INITIAL_PAYLOAD, INITIAL_HEADERS, HEADERS, PAYLOAD_TEMPLATE, CHECK_URL_YARL

# Constants
MIN_PLATE_LENGTH = 2
MAX_PLATE_LENGTH = 7
OPENAI_MODEL = "gpt-3.5-turbo"  # Define constant for OpenAI model


def load_plates_from_text(filepath: str) -> List[str]:
    """
    Load potential license plates from a text file.
    
    Args:
        filepath (str): Path to the text file containing potential plate values.
        
    Returns:
        List[str]: A sorted list of valid plate candidates filtered by length and sorted.
    """
    # If file exists, open it
    if os.path.exists(filepath):
        # Load the modern word list
        with open(filepath) as f:
            all_words = f.read().splitlines()

        # Filter words of length 1 to 7
        test_list = [word.lower() for word in all_words if MIN_PLATE_LENGTH <= len(word) <= MAX_PLATE_LENGTH]
        
        # Sort by length (descending), then alphabetically
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
    
    # Ensure the file has a .csv extension
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

    
async def generate_plates_from_topic(topic: str, num_plates: int) -> List[str]:
    """
    Generate a list of potential license plates based on a given topic using OpenAI.

    Args:
        topic (str): The topic to base the license plates on (e.g., "animals").
        num_plates (int): Number of plates to generate, defaults to 10.

    Returns:
        List[str]: A list of generated plate candidates filtered by length.
    """
    # Load environment variables from .env file.
    load_dotenv()
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file.")

    # Initialize OpenAI client.
    client = AsyncOpenAI(api_key=api_key)

    # Define the prompt for OpenAI.
    prompt = (
        f"Generate a list of {num_plates} creative license plate ideas related to '{topic}'. "
        f"Each plate must be between {MIN_PLATE_LENGTH} and {MAX_PLATE_LENGTH} characters long, "
        "using only letters and numbers. Return only the list, one plate per line."
        "Do not number the list, or include any other characters."
    )

    try:
        # Make the API call asynchronously.
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        # Extract the generated plates.
        plates = response.choices[0].message.content.strip().splitlines()
        # Filter and clean the list.
        valid_plates = [
            plate.strip().lower() for plate in plates
            if MIN_PLATE_LENGTH <= len(plate.strip()) <= MAX_PLATE_LENGTH and plate.strip().isalnum()
        ]
        print(f"\nGenerated {len(valid_plates)} valid plates for topic '{topic}': {valid_plates}\n")
        return valid_plates

    except Exception as e:
        print(f"Failed to generate plates with OpenAI: {str(e)}")
        return []

class Worker:
    """
    Worker class for handling asynchronous license plate availability checks.
    
    Each worker maintains its own session with the DMV website and processes
    tasks from a shared queue.
    """
    
    def __init__(self, session: aiohttp.ClientSession, queue: asyncio.Queue):
        """
        Initialize a Worker instance.
        
        Args:
            session (aiohttp.ClientSession): An established HTTP session.
            queue (asyncio.Queue): The shared task queue.
        """
        self.session = session
        self.queue = queue
        # Retrieve the JSESSIONID cookie from the session
        self.id = self.session.cookie_jar.filter_cookies(CHECK_URL_YARL).get("JSESSIONID").value
        print(f"Worker initiated with JSESSIONID: {self.id}")

    @classmethod
    async def create(cls, queue: asyncio.Queue) -> 'Worker':
        """
        Asynchronously initializes a worker with an active session.
        
        Args:
            queue (asyncio.Queue): The shared task queue.
            
        Returns:
            Worker: A new Worker instance with an initialized session.
            
        Raises:
            Exception: If session initialization fails with detailed error info.
        """
        session = aiohttp.ClientSession()
        
        try:
            async with session.post(CHECK_URL_YARL, data=INITIAL_PAYLOAD, headers=INITIAL_HEADERS) as resp:
                if resp.status != 200:
                    raise Exception(f"Failed to initialize session: HTTP {resp.status}")
                await resp.json(content_type=None)  # Simulates T&C agreement
        except aiohttp.ClientConnectionError as e:
            await session.close()
            raise Exception(f"Network error during session initialization: {str(e)}")
        except Exception as e:
            await session.close()
            raise Exception(f"Error initializing session: {str(e)}")

        return cls(session, queue)
    
    
    async def process_task(self) -> Dict[str, str]:
        """
        Process plate check tasks from the queue until None is received.
        
        Returns:
            Dict[str, str]: Dictionary of processed plate numbers and their status.
        """
        results = {}
        while True:
            plate_number = await self.queue.get()
            if plate_number is None:
                self.queue.task_done()
                break
            status = await self.get_plate_status(plate_number)
            results[plate_number] = status
            self.queue.task_done()
        return results
        
       
    def update_payload(self, plate_number: str) -> Dict[str, str]:
        """
        Create a payload for the plate check request.
        
        Args:
            plate_number (str): The license plate to check.
            
        Returns:
            Dict[str, str]: The payload dictionary for the HTTP request.
        """
        new_payload = PAYLOAD_TEMPLATE.copy()
        for i, character in enumerate(plate_number):
            new_payload[f'plateChar{i}'] = character
        return new_payload 
           
    async def get_plate_status(self, plate: str) -> str:
        """
        Check if a plate is available.
        
        Args:
            plate (str): The license plate to check.
            
        Returns:
            str: The status of the plate (e.g., "AVAILABLE", "UNAVAILABLE").
        """
        new_payload = self.update_payload(plate)
        
        async with self.session.post(CHECK_URL_YARL, data=new_payload, headers=HEADERS) as resp:
            response_json = await resp.json(content_type=None)
            
        plate_status = response_json.get("code", "UNKNOWN")
        
        if plate_status == "AVAILABLE":
            print(f"{Fore.GREEN}{plate.upper()}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{plate.upper()}{Style.RESET_ALL}")
            
        return plate_status

    async def close(self) -> None:
        """
        Close the HTTP session.
        
        Returns:
            None
        """
        await self.session.close()


async def main(input_file: Optional[str], output_file: str, workers: int, topic: Optional[str] = None, num_plates: Optional[int] = None) -> None:
    """
    Process license plate availability checks using multiple workers.

    Args:
        input_file (Optional[str]): Path to the input file containing plate numbers.
        output_file (str): Path to the output CSV file for results.
        workers (int): Number of concurrent workers to use.
        topic (Optional[str]): Topic for generating plates with OpenAI, if provided.
        num_plates (Optional[int]): Number of plates to generate if topic is used.

    Returns:
        None
    """
    # Record the start time for performance measurement.
    start_time: float = time()
    
    # Load or generate plate numbers.
    if topic:
        plates: List[str] = await generate_plates_from_topic(topic, num_plates)
    else:
        plates: List[str] = load_plates_from_text(input_file)

    if not plates:
        print("No plates to process. Exiting.")
        return

    # Initialize the task queue for workers.
    queue: asyncio.Queue = asyncio.Queue()
    
    # Print a full-width separator line.
    terminal_width = shutil.get_terminal_size().columns
    print("-" * terminal_width)
    
    # Create and initialize worker instances.
    worker_instances: List[Worker] = await asyncio.gather(
        *(Worker.create(queue) for _ in range(workers))
    )
    
    # Print another full-width separator line with a newline.
    print("-" * terminal_width, "\n")
    
    print("Searching for valid plates:\n")
    
    # Add plate numbers to the queue for processing.
    for plate in plates:
        await queue.put(plate)
    
    # Add None values to signal workers to stop.
    for _ in range(workers):
        await queue.put(None)
    
    # Create and run worker tasks.
    tasks = [asyncio.create_task(worker.process_task()) for worker in worker_instances]
    results: List[Dict[str, str]] = await asyncio.gather(*tasks)
    
    # Close all worker sessions.
    for worker in worker_instances:
        await worker.close()
    
    # Combine results from all workers.
    final_results: Dict[str, str] = {}
    for result_dict in results:
        final_results.update(result_dict)
    
    # Calculate and display the total execution time.
    end_time: float = time()
    total_duration: float = end_time - start_time
    print(f"\nTotal Time: {total_duration:.2f} seconds")
    
    # Save the results to the output file.
    save_to_file(final_results, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check California DMV license plate availability.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--input", type=str, help="Input file containing plate numbers.")
    group.add_argument("-t", "--topic", type=str, help="Topic for generating plates with OpenAI (e.g., 'animals').")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output CSV file for results.")
    parser.add_argument("-n", "--num-plates", type=int, help="Number of plates to generate (required if topic is used).")
    parser.add_argument("-w", "--workers", type=int, default=10, help="Number of concurrent workers (optional, default=10).")

    args = parser.parse_args()
    
    if args.topic and args.num_plates is None:
        parser.error("When using -t/--topic, you must specify -n/--num-plates.")
    
    asyncio.run(main(args.input, args.output, args.workers, args.topic, args.num_plates))

