"""
plate_generator.py

This file contains functionality for generating license plate ideas using OpenAI based on a given topic.
"""

import asyncio
from typing import List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

# Constants
MIN_PLATE_LENGTH: int = 2
MAX_PLATE_LENGTH: int = 7
OPENAI_MODEL: str = "gpt-3.5-turbo"


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
        "Do not use the number 0 (zero) in any plate."
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