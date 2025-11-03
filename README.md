# Streamlit OpenAlex

A Streamlit web application that provides an interface to search for academic works using the [OpenAlex API](https://docs.openalex.org/).

## Features

- 🔍 Search for academic works by keywords
- 📊 Configurable results per page (5-50)
- 📄 Pagination support
- 📚 Display work details including:
  - Title
  - Authors
  - Publication year
  - Publication venue
  - Citation count
  - DOI and OpenAlex ID links

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

1. Enter your search query in the text box (e.g., "machine learning", "climate change", "quantum computing")
2. Adjust the results per page slider (5-50 results)
3. Use the page number input to navigate through results
4. Click the "🔍 Search" button to perform the search
5. Browse the results with links to DOI and OpenAlex pages

## About OpenAlex

[OpenAlex](https://openalex.org) is a free and open catalog of scholarly papers, authors, institutions, and more. It provides comprehensive metadata about academic works and is a great resource for research and academic analysis.

## API Documentation

For more information about the OpenAlex API, visit the [official documentation](https://docs.openalex.org/).
