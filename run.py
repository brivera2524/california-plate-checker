"""
run.py

A convenience wrapper to run the plate_checker package.
For proper usage, use: python -m plate_checker
"""

import sys
from plate_checker.__main__ import main
import asyncio
import argparse
from plate_checker.config import DEFAULT_NUM_WORKERS

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check California DMV license plate availability.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--input", type=str, help="Input file containing plate numbers.")
    group.add_argument("-t", "--topic", type=str, help="Topic for generating plates with OpenAI (e.g., 'animals').")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output CSV file for results.")
    parser.add_argument("-n", "--num-plates", type=int, help="Number of plates to generate (required if topic is used).")
    parser.add_argument("-w", "--workers", type=int, default=DEFAULT_NUM_WORKERS, help="Number of concurrent workers (optional, default=10).")

    args = parser.parse_args()
    
    if args.topic and args.num_plates is None:
        parser.error("When using -t/--topic, you must specify -n/--num-plates.")
    
    asyncio.run(main(args.input, args.output, args.workers, args.topic, args.num_plates)) 