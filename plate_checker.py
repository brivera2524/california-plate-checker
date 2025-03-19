import asyncio
import aiohttp
from colorama import Fore, Style
import os
import csv
from config import INITIAL_PAYLOAD, INITIAL_HEADERS, HEADERS, PAYLOAD_TEMPLATE, CHECK_URL
import argparse

def load_plates_from_text(filepath):
    # If file exists, open it
    if os.path.exists(filepath):
        # Load the modern word list
        with open(filepath) as f:
            all_words = f.read().splitlines()

        # Filter words of length 1 to 7
        test_list = [word.lower() for word in all_words if 2 <= len(word) <= 7]
        
        # Sort by length (descending), then alphabetically
        test_list = sorted(test_list, key=lambda word: (-len(word), word))

        print(f"Total words found: {len(test_list)}")
        
        return test_list
        
    else:
        print("Failed to Find text file.")
        quit()
        
def save_to_file(results, save_file_path):
    # 'results' is a dictionary mapping plate to status.
    # Convert dictionary items to a list and sort alphabetically by plate.
    sorted_results = sorted(results.items(), key=lambda x: x[0])
    
    with open(save_file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Plate", "Status"])
        # Write only available plates (or adjust as needed)
        for plate, status in sorted_results:
            writer.writerow([plate, status])

    
class Worker:
    def __init__(self, session: aiohttp.ClientSession, queue: asyncio.Queue):
        self.session = session
        self.queue = queue
        # Retrieve the JSESSIONID cookie from the session
        self.id = self.session.cookie_jar.filter_cookies(CHECK_URL).get("JSESSIONID").value
        print(f"Worker initiated with JSESSIONID: {self.id}")

    @classmethod
    async def create(cls, queue: asyncio.Queue):
        """Asynchronously initializes a worker with an active session."""
        session = aiohttp.ClientSession()
        

        try:
            async with session.post(CHECK_URL, data=INITIAL_PAYLOAD, headers=INITIAL_HEADERS) as resp:
                await resp.json(content_type=None)  # Simulates T&C agreement
        except Exception as e:
            print(f"Error initializing session: {e}")
            await session.close()
            raise

        return cls(session, queue)
    
    
    async def process_task(self):
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
        
       
    def update_payload(self, plate_number):
        new_payload = PAYLOAD_TEMPLATE.copy()
        for i, character in enumerate(plate_number):
            new_payload[f'plateChar{i}'] = character
        return new_payload 
           
    async def get_plate_status(self, plate):
        """Check if a plate is available."""
        new_payload = self.update_payload(plate)
        
        async with self.session.post(CHECK_URL, data=new_payload, headers=HEADERS) as resp:
            response_json = await resp.json(content_type=None)
            
        plate_status = response_json.get("code", "UNKNOWN")
        
        if plate_status == "AVAILABLE":
            print(f"{Fore.GREEN}{plate.upper()}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{plate.upper()}")
            
        return plate_status

    async def close(self):
        await self.session.close()


async def main(input_file, output_file, num_workers):
    plates = load_plates_from_text(input_file)
    queue = asyncio.Queue()
    workers = await asyncio.gather(*(Worker.create(queue) for _ in range(num_workers)))
    
    for plate in plates:
        await queue.put(plate)
    for _ in range(num_workers):
        await queue.put(None)
    
    tasks = [asyncio.create_task(worker.process_task()) for worker in workers]
    results = await asyncio.gather(*tasks)
    
    for worker in workers:
        await worker.close()
    
    final_results = {}
    for d in results:
        final_results.update(d)
    
    save_to_file(final_results, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check California DMV license plate availability.")
    parser.add_argument("-i", "--input", type=str, help="Input file containing plate numbers.")
    parser.add_argument("-o", "--output", type=str, help="Output CSV file for results.")
    parser.add_argument("-w", "--workers", type=int, help="Number of concurrent workers.")

    args = parser.parse_args()
    asyncio.run(main(args.input, args.output, args.workers))
