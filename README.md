# California License Plate Checker

A Python tool to check California license plate combinations against a list of common words to find potentially interesting or meaningful combinations.

## Features

- Checks California license plate combinations against a list of common words
- Generates CSV output with matching results
- Supports 7-character plate format
- Filters out words that don't match the valid plate length
- Can use any text file as input for word combinations

## Requirements

- Python 3.x
- aiohttp>=3.8.0
- colorama>=0.4.6

## Usage

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Prepare a text file with words to check (one word per line)
4. Run the script: `python plate_checker.py`

The script will generate a `results.csv` file containing matching plate combinations.

## License

MIT License 