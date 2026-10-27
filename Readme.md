# Yandex Map Parser

A Python scraper that searches Yandex Maps for a given keyword and exports
the results — name, location, phone number, and rating score — to an Excel file.

## Features

- Search Yandex Maps with a user-defined keyword
- Extract for each result:
  - **Name** of the place
  - **Location / address**
  - **Phone number**
  - **Rating score**
- Save all collected data to an `.xlsx` file
- Simple CLI-based usage

## Requirements

- Python 3.8 or higher
- Google Chrome (if using Selenium-based scraping)
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/caoguru/yandexmap_parser.git
   cd yandexmap_parser