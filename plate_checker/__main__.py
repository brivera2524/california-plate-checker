"""
__main__.py

This file serves as the entry point for the California license plate checker application,
orchestrating the plate checking process using multiple workers.
"""

import asyncio
import argparse
from typing import List, Dict, Optional
import shutil
from time import time
from .utils import load_plates_from_text, save_to_file
from .plate_generator import generate_plates_from_topic
from .worker import Worker


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