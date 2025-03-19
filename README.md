# California License Plate Checker

This Python script automates the process of checking license plate availability via the California DMV website. It uses asyncio and aiohttp to perform high-speed, parallel requests, ensuring efficient validation of multiple plates at once. Results are saved to a CSV file for easy review.


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
python plate_checker.py -i plates.txt -o results.csv -w 5 
```

### Arguments
| Argument | Description | Default |
|----------|-------------|---------|
| `-i` | Input file with plate numbers | `common.txt` |
| `-o` | Output CSV file | `results.csv` |
| `-w` | Number of workers | `10` |


### Notes

- This script is for educational purposes only. Use it responsibly and ensure compliance with applicable laws and terms of service.
- I am not sure what the ideal number of workers is, but 10 seems to go decently fast.

