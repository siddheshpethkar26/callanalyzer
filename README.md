# SquareYards Project Scraper

This repository contains a simple Selenium-based web scraper for collecting real estate project details from [SquareYards](https://www.squareyards.com/).

## Features

- Crawls project listings with pagination support.
- Extracts details such as project name, price, configuration, amenities, images, and more.
- Saves media URLs in folders named after the project.
- Outputs scraped data to CSV and JSON formats.
- Supports headless execution and optional proxy rotation.

## Requirements

- Python 3.8+
- Google Chrome browser and ChromeDriver installed and available in `PATH`.
- Python packages listed in `requirements.txt`.

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper with:

```bash
python squareyards_scraper.py [--city CITY] [--url URL] [--limit N] [--output FILE]
```

Use `--city` to target a specific city (for example `--city Mumbai`). The scraper will generate both CSV and JSON files (the JSON file uses the same name as the CSV but with a `.json` extension). Example:

```bash
python squareyards_scraper.py --city Mumbai --limit 50 --output mumbai_projects.csv
```

Without any arguments the scraper defaults to Indian-wide listings and saves the first 10 projects to `sample_output.csv`.

## Sample Output

Example entries for 10 projects are provided in `sample_output.csv` and `sample_output.json`.

## Disclaimer

This scraper is provided for educational purposes. Ensure you comply with the website's terms of service before scraping large amounts of data.
