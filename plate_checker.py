import asyncio
import aiohttp
from colorama import Fore, Style
import os
import csv


def load_plates_from_text(filepath):
    # If file exists, open it
    if os.path.exists(filepath):
        # Load the modern word list
        with open(filepath) as f:
            all_words = f.read().splitlines()

        # Filter words of length 1 to 7
        test_list = [word.lower() for word in all_words if len(word)==7]
        
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
    


# Define Headers (taken from browser cURL request), Not entirely sure what is necessary
headers = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.dmv.ca.gov",
    "Referer": "https://www.dmv.ca.gov/wasapp/ipp2/startPers.do",
    "Sec-Ch-Ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

# Define Payload Template
payload_template = {
    "plateType": "Z",
    "kidsPlate": "",
    "plateNameLow": "california 1960s legacy",
    "plateName": "California 1960s Legacy",
    "plateLength": "7",
    "vetDecalCd": "",
    "centeredPlateLength": "0",
    "platechecked": "no",
    "imageSelected": "none",
    "vehicleType": "AUTO",
    "plateChar0": "",
    "plateChar1": "",
    "plateChar2": "",
    "plateChar3": "",
    "plateChar4": "",
    "plateChar5": "",
    "plateChar6": "",
    "plateChar7": "",
    "plateChar8": "",
    "plateChar9": "",
    "plateChar10": "",
    "plateChar11": "",
    "plateChar12": "",
    "plateChar13": "",
    "vetDecalDesc": ""
}

init_url = "https://www.dmv.ca.gov/wasapp/ipp2/initPers.do" 
url = "https://www.dmv.ca.gov/wasapp/ipp2/checkPers.do"



        
 # Creates a new session to store JSESSIONIDs, necessary for validation.   
async def init_session():
    session = aiohttp.ClientSession()
    
    # Simulates agreeing to T&Cs
    payload = {
        "acknowledged": "true", 
        "_acknowledged": "on" 
    }
    headers = {
        "Referer": init_url,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    }
    
    # "Click" continue, gets the JSESSIONID to validate plate requests
    async with session.post(url, data=payload, headers=headers) as resp:
        await resp.json(content_type=None)
    
    return session
    
    
# Worker Class, grabs tasks from queue  
class Worker:
    
    def __init__(self, session: aiohttp.ClientSession, queue: asyncio.Queue):
        self.session = session
        self.queue = queue
        # Retrieve the JSESSIONID cookie from the session
        self.id = self.session.cookie_jar.filter_cookies(url).get("JSESSIONID").value
        print(f"Worker initiated with JSESSIONID: {self.id}")

    @classmethod
    async def create(cls, queue: asyncio.Queue):
        # Asynchronously initialize the session.
        session = await init_session()
        return cls(session, queue)

    async def process_task(self):
        results = {}
        while True:
            plate_number = await self.queue.get()
            if plate_number is None:  # Sentinel to stop processing
                self.queue.task_done()
                break
            status = await get_plate_status(self.session, plate_number)
            results[plate_number] = status
            self.queue.task_done()
        return results
        
    async def close(self):
        await self.session.close()
    
    
    
def update_payload(plate_number):
    """
    Creates a fresh payload for the given plate number.
    """
    new_payload = payload_template.copy()
    # Reset plateChar fields
    for i in range(7):
        new_payload[f'plateChar{i}'] = ""
    # Populate with characters from the plate_number
    for i, character in enumerate(plate_number):
        new_payload[f'plateChar{i}'] = character
        
    return new_payload
    
    
  
async def get_plate_status(session: aiohttp.ClientSession, plate):
    
    # Create a payload for the specified plate
    new_payload = update_payload(plate)
    
    # Make the request
    async with session.post(url, data=new_payload, headers = headers) as resp:
        response_json = await resp.json(content_type=None)
    plate_status = response_json.get("code", "UNKNOWN")
    if plate_status == "AVAILABLE":
        print(f"{Fore.GREEN}{plate.upper()}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}{plate.upper()}")
        
    return plate_status
    
async def main():
    
    # Load plates from a text file
    plates = load_plates_from_text("common.txt")
    plates = plates[:1000]
    
    #Instantiate Queue
    queue = asyncio.Queue()
    
    num_workers = 10 # Change this to set the number of workers
    
    # Create worker instances concurrently
    workers = await asyncio.gather(*(Worker.create(queue) for _ in range(num_workers)))
    
    # Enqueue tasks
    for plate in plates:
        await queue.put(plate)
    
    # Enqueue one sentinel per worker to signal termination
    for _ in range(num_workers):
        await queue.put(None)
    
    # Create tasks for each worker's process loop and wait for them concurrently
    tasks = [asyncio.create_task(worker.process_task()) for worker in workers]
    results = await asyncio.gather(*tasks)
    
    # Close all sessions
    for worker in workers:
        await worker.close()
        
    final_results = {}
    for d in results:
        final_results.update(d)
        
    save_to_file(final_results, "results.csv")
        
    

asyncio.run(main())
