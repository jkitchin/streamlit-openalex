# Streamlit OpenAlex

A Streamlit web application for searching academic works and authors using the [OpenAlex API](https://docs.openalex.org/).

## Features

- **Search Works**: Search for academic papers by keywords with:
  - Configurable results per page (5-50)
  - Pagination support
  - Display work details including title, authors, publication year, publication venue, citation count
  - DOI and OpenAlex ID links

- **Search Authors**: Search for researchers and view:
  - Name, ORCID, and institutional affiliation
  - Publication count and citation metrics
  - h-index and i10-index
  - Research areas and concepts

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jkitchin/streamlit-openalex.git
cd streamlit-openalex
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`.

## How to Use

### Search Works Tab
1. Enter your search query in the text box (e.g., "machine learning", "climate change", "quantum computing")
2. Adjust the results per page slider (5-50 results)
3. Use the page number input to navigate through results
4. Click the "🔍 Search" button to perform the search
5. Browse the results with links to DOI and OpenAlex pages

### Search Authors Tab
1. Enter author names or institutions to find researchers
2. Adjust results per page as needed
3. View comprehensive author metrics including publication counts, citations, h-index, i10-index
4. Access ORCID profiles and OpenAlex pages

## About OpenAlex

[OpenAlex](https://openalex.org) is a free and open catalog of scholarly papers, authors, institutions, and more. It provides comprehensive metadata about academic works and is a great resource for research and academic analysis.

## API Documentation

For more information about the OpenAlex API, visit the [official documentation](https://docs.openalex.org/).

## Practice Repository

This is a practice repo for copilot and claude code in the cloud.
