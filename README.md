# California License Plate Checker

This Python script automates the process of checking license plate availability via the California DMV website. It uses asyncio and aiohttp to perform high-speed, parallel requests, ensuring efficient validation of multiple plates at once. Results are saved to a CSV file for easy review.

## Features
- Asynchronous Processing: Uses asyncio and aiohttp for efficient, non-blocking requests.

- Multi-Worker Support: Allows multiple concurrent requests to speed up plate availability checks.

- Filters plate numbers from a text file, only keeping valid CA license plates (2-7 characters) before processing.

- AI-Powered Plate Generation: Integrates with OpenAI to generate creative license plate suggestions based on a topic.

- CSV Output: Saves results in a structured CSV format for easy review and analysis.

- Tested with up to 100 simultaneous workers, averaging 152 plate checks per second across 6550 plates.


## Requirements

- Python 3.x
- aiohttp>=3.8.0
- colorama>=0.4.6
- openai>=1.42.0
- python-dotenv>=1.0.1


## Usage

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Choose one of the following input methods:
   - Add a text file with plate numbers (each on a separate line)
   - Set up OpenAI integration to generate plate ideas based on a topic
4. If using OpenAI to generate plates, create a `.env` file with your API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
5. Run the script with one of the following options:

```bash
# Using a text file with plate numbers
python plate_checker.py -i plates.txt -o results.csv -w 5 

# Using OpenAI to generate plates based on a topic
python plate_checker.py -t animals -n 20 -o results.csv -w 5
```

### Arguments
| Argument | Short | Long | Description | Default |
|----------|-------|------|-------------|---------|
| `-i` | `--input` | Input file with plate numbers | Required if not using `-t` |
| `-t` | `--topic` | Topic for generating plates with OpenAI | Required if not using `-i` |
| `-n` | `--num-plates` | Number of plates to generate when using `-t` | Required with `-t` |
| `-o` | `--output` | Output CSV file | Required |
| `-w` | `--workers` | Number of concurrent workers | `10` |


### Notes

- This script is for educational purposes only. Use it responsibly and ensure compliance with applicable laws and terms of service.
- The optimal number of workers may vary based on internet speed and DMV rate limits. From testing, 10 workers provide a good balance between speed and avoiding potential request blocks.
- Each worker gets its own session (JSESSIONID) to prevent mismatched plate statuses.
- Workers process one request at a time to ensure accurate results.
- When using the OpenAI integration, the script uses the GPT-3.5 Turbo model to generate creative license plate ideas.
