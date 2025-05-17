"""
worker.py

This file defines the Worker class for handling asynchronous license plate availability checks with the California DMV.
"""

import asyncio
import aiohttp
from typing import Dict, Any
from colorama import Fore, Style
from .config import CHECK_URL_YARL, INITIAL_PAYLOAD, INITIAL_HEADERS, HEADERS, PAYLOAD_TEMPLATE


class Worker:
    """
    Worker class for handling asynchronous license plate availability checks.
    
    Each worker maintains its own session with the DMV website and processes
    tasks from a shared queue.
    """
    
    def __init__(self, session: aiohttp.ClientSession, queue: asyncio.Queue) -> None:
        """
        Initialize a Worker instance.
        
        Args:
            session (aiohttp.ClientSession): An established HTTP session.
            queue (asyncio.Queue): The shared task queue.
        """
        self.session = session
        self.queue = queue
        # Retrieve the JSESSIONID cookie from the session.
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
                await resp.json(content_type=None)  # Simulates T&C agreement.
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