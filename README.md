# Next in Tech 2026 - Job Market Scraping

Project developed for the Next in Tech 2026 Boolean event.

## Overview

This project collects tech job postings from multiple job boards and stores them in a shared SQLite database (`job_postings.db`) for analysis.

## Notebooks

- `nofluff.ipynb`: queries the NoFluffJobs search API and stores the results in the `nofluff` table.
- `tech_compenso.ipynb`: scrapes job cards from techcompenso.com with Selenium and stores them in the `techcompenso` table.

## Data collected

Each posting includes title, company, location, work mode, salary range (min/max), tags and a link to the full description.

## Requirements

See `requirements.txt` for the Python dependencies (httpx, pandas, selenium, ipykernel).
