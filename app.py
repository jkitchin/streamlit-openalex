"""
Streamlit app for searching OpenAlex works.

This app provides an interface to search for academic works using the OpenAlex API.
"""

import streamlit as st
import requests
from typing import Dict, List, Any


def search_openalex_works(query: str, per_page: int = 10, page: int = 1) -> Dict[str, Any]:
    """
    Search for works in OpenAlex API.
    
    Args:
        query: Search query string
        per_page: Number of results per page (default: 10)
        page: Page number (default: 1)
    
    Returns:
        Dictionary containing the API response
    """
    base_url = "https://api.openalex.org/works"
    
    params = {
        "search": query,
        "per-page": per_page,
        "page": page,
    }
    
    headers = {
        "User-Agent": "mailto:streamlit-openalex-app@example.com"  # Polite pool
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from OpenAlex API: {e}")
        return {}


def display_work(work: Dict[str, Any]) -> None:
    """
    Display a single work in the Streamlit UI.
    
    Args:
        work: Dictionary containing work data from OpenAlex API
    """
    # Title
    title = work.get("title", "No title available")
    st.markdown(f"### {title}")
    
    # Authors
    authorships = work.get("authorships", [])
    if authorships:
        authors = []
        for authorship in authorships[:5]:  # Limit to first 5 authors
            author = authorship.get("author", {})
            author_name = author.get("display_name", "Unknown")
            authors.append(author_name)
        
        if len(authorships) > 5:
            authors.append("et al.")
        
        st.write(f"**Authors:** {', '.join(authors)}")
    
    # Publication year
    pub_year = work.get("publication_year")
    if pub_year:
        st.write(f"**Year:** {pub_year}")
    
    # Publication venue
    primary_location = work.get("primary_location", {})
    source = primary_location.get("source", {})
    source_name = source.get("display_name")
    if source_name:
        st.write(f"**Published in:** {source_name}")
    
    # Citation count
    cited_by_count = work.get("cited_by_count", 0)
    st.write(f"**Citations:** {cited_by_count}")
    
    # DOI and OpenAlex ID links
    col1, col2 = st.columns(2)
    
    with col1:
        doi = work.get("doi")
        if doi:
            st.markdown(f"[DOI Link]({doi})")
    
    with col2:
        openalex_id = work.get("id")
        if openalex_id:
            st.markdown(f"[OpenAlex]({openalex_id})")
    
    st.divider()


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="OpenAlex Works Search",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 OpenAlex Works Search")
    st.markdown("""
    Search for academic works using the [OpenAlex API](https://docs.openalex.org/).
    OpenAlex is a free and open catalog of scholarly papers, authors, institutions, and more.
    """)
    
    # Search input
    search_query = st.text_input(
        "Enter your search query:",
        placeholder="e.g., machine learning, climate change, quantum computing",
        help="Enter keywords to search for academic works"
    )
    
    # Search options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        results_per_page = st.slider(
            "Results per page:",
            min_value=5,
            max_value=50,
            value=10,
            step=5
        )
    
    with col2:
        page_number = st.number_input(
            "Page:",
            min_value=1,
            max_value=100,
            value=1,
            step=1
        )
    
    # Search button
    if st.button("🔍 Search", type="primary") or search_query:
        if search_query:
            with st.spinner("Searching OpenAlex..."):
                results = search_openalex_works(
                    query=search_query,
                    per_page=results_per_page,
                    page=page_number
                )
            
            if results and "results" in results:
                works = results["results"]
                meta = results.get("meta", {})
                total_count = meta.get("count", 0)
                
                # Display results summary
                st.success(f"Found {total_count:,} works")
                
                # Display each work
                if works:
                    st.markdown("---")
                    for idx, work in enumerate(works, start=1):
                        st.markdown(f"#### Result {idx}")
                        display_work(work)
                else:
                    st.info("No results found for your query.")
            else:
                st.warning("No results returned. Please try a different query.")
        else:
            st.warning("Please enter a search query.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
        <small>
        Data from <a href="https://openalex.org" target="_blank">OpenAlex</a> | 
        <a href="https://docs.openalex.org/" target="_blank">API Documentation</a>
        </small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
