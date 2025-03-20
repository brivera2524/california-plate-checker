# California License Plate Checker

This Python script automates the process of checking license plate availability via the California DMV website. It sends asynchronous POST requests directly to the DMV server using asyncio and aiohttp, eliminating the need for slower tools like Selenium or headless browsers. The result is a highly efficient, non-blocking validation process capable of rapidly handling multiple simultaneous requests. Results are saved to a CSV file for easy review.

## Features
- Asynchronous Processing: Uses asyncio and aiohttp for efficient, non-blocking requests.

- Multi-Worker Support: Allows multiple concurrent requests to speed up plate availability checks.

- Filters plate numbers from a text file, only keeping valid CA license plates (2-7 characters) before processing.

- CSV Output: Saves results in a structured CSV format for easy review and analysis.

- Tested with up to 100 simulataneous workers, averaging 152 plate checks per second across 6550 plates.


## Requirements

- Python 3.x
- aiohttp>=3.8.0
- colorama>=0.4.6


## Usage

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. (Optional) Add a text file with plate numbers on individual lines to the directory
4. Run the script with:
```bash
python plate_checker.py -i common.txt -o results.csv -w 10 
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `-i` | Input file with plate numbers | `common.txt` |
| `-o` | Output CSV file | `results.csv` |
| `-w` | Number of workers | `10` |


### Notes

- This script is for educational purposes only. Use it responsibly and ensure compliance with applicable laws and terms of service.
- The optimal number of workers may vary based on internet speed and DMV rate limits. From testing, 100 workers processed common.txt in about 43 seconds, averaging 152 checks per second. The amount of workers could likely be increased, as I did not encounter any rate limiting. However, I would not recommend exceeding this number to avoid abusing the DMV's server.
