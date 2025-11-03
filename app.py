"""
Streamlit app for searching OpenAlex works and authors.

This app provides an interface to search for academic works and authors
using the OpenAlex API.
"""

import streamlit as st
import requests
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import statistics


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
        "User-Agent": "mailto:user@example.com"  # Polite pool access
    }

    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from OpenAlex API: {e}")
        return {}


def search_openalex_authors(query: str, per_page: int = 20) -> Optional[Dict]:
    """
    Search for authors in OpenAlex API.

    Args:
        query: Search query string
        per_page: Number of results per page (default: 20)

    Returns:
        Dictionary containing the API response
    """
    url = "https://api.openalex.org/authors"
    params = {
        "search": query,
        "per_page": per_page,
    }

    headers = {
        "User-Agent": "mailto:user@example.com"  # Polite pool access
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error searching authors: {e}")
        return None


def autocomplete_authors(query: str) -> Optional[List[Dict]]:
    """
    Get autocomplete suggestions for author names using OpenAlex API.

    This endpoint is optimized for fast type-ahead style search.

    Args:
        query: Partial author name to autocomplete

    Returns:
        List of author suggestion dictionaries, or None if error occurs
    """
    if not query or len(query) < 2:
        return []

    url = "https://api.openalex.org/autocomplete/authors"
    params = {"q": query}

    headers = {
        "User-Agent": "mailto:user@example.com"  # Polite pool access
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching autocomplete suggestions: {e}")
        return []


def fetch_author_works(author_id: str, per_page: int = 200) -> Optional[List[Dict]]:
    """
    Fetch all works for a specific author from OpenAlex API.

    Supports pagination to retrieve all works beyond the 200-result limit.

    Args:
        author_id: OpenAlex author ID (e.g., 'A1234567890' or full URL)
        per_page: Number of results per page (default: 200, max allowed)

    Returns:
        List of work dictionaries, or None if error occurs
    """
    # Extract the author ID from the full URL if needed
    if 'openalex.org' in author_id:
        author_id = author_id.split('/')[-1]

    url = "https://api.openalex.org/works"
    params = {
        "filter": f"author.id:{author_id}",
        "per_page": per_page,
        "sort": "publication_year:asc",
    }

    headers = {
        "User-Agent": "mailto:user@example.com"
    }

    all_works = []
    page = 1

    try:
        while True:
            params["page"] = page
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])
            if not results:
                break

            all_works.extend(results)

            # Check if we've got all results
            meta = data.get('meta', {})
            if len(all_works) >= meta.get('count', 0):
                break

            page += 1

            # Safety limit to avoid infinite loops
            if page > 50:
                break

        return all_works if all_works else []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching author works: {e}")
        return None


def calculate_academic_age(author: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate academic age and confidence score for an author.

    Uses publication density analysis to find the first year of sustained activity,
    combined with temporal and topic consistency checks.

    Args:
        author: Author dictionary from OpenAlex API

    Returns:
        Dictionary containing:
        - academic_age: Years since sustained activity began
        - confidence_score: 0-100 confidence percentage
        - confidence_level: 'High', 'Medium', or 'Low'
        - first_pub_year: Year of first publication in sustained activity
        - earliest_pub_year: Absolute earliest publication year
        - excluded_pubs: Number of publications excluded as outliers
        - notes: Explanation of calculation
    """
    current_year = datetime.now().year
    author_id = author.get('id', '')

    # Fetch author's works
    works = fetch_author_works(author_id)

    if not works or len(works) == 0:
        return {
            'academic_age': None,
            'confidence_score': 0,
            'confidence_level': 'N/A',
            'first_pub_year': None,
            'earliest_pub_year': None,
            'excluded_pubs': 0,
            'notes': 'No publications found'
        }

    # Extract publication years
    pub_years = []
    for work in works:
        year = work.get('publication_year')
        if year and year > 1900 and year <= current_year:  # Sanity check
            pub_years.append(year)

    if not pub_years:
        return {
            'academic_age': None,
            'confidence_score': 0,
            'confidence_level': 'N/A',
            'first_pub_year': None,
            'earliest_pub_year': None,
            'excluded_pubs': 0,
            'notes': 'No valid publication years found'
        }

    pub_years.sort()
    earliest_year = pub_years[0]

    # Count publications per year
    year_counts = defaultdict(int)
    for year in pub_years:
        year_counts[year] += 1

    # Find first year of sustained activity (at least 2 pubs within any 3-year window)
    sustained_start_year = None
    for year in range(earliest_year, current_year + 1):
        pubs_in_window = sum(year_counts.get(y, 0) for y in range(year, year + 3))
        if pubs_in_window >= 2:
            sustained_start_year = year
            break

    # If no sustained activity found, use earliest year
    if sustained_start_year is None:
        sustained_start_year = earliest_year

    # Calculate academic age
    academic_age = current_year - sustained_start_year

    # Count excluded publications (before sustained activity)
    excluded_pubs = sum(1 for y in pub_years if y < sustained_start_year)

    # Calculate confidence score components
    confidence_components = []

    # 1. Temporal consistency (40% weight)
    # Check for large gaps before sustained activity
    gap_before_sustained = sustained_start_year - earliest_year
    if gap_before_sustained == 0:
        temporal_score = 1.0
    elif gap_before_sustained <= 2:
        temporal_score = 0.9
    elif gap_before_sustained <= 5:
        temporal_score = 0.7
    elif gap_before_sustained <= 10:
        temporal_score = 0.5
    else:
        temporal_score = 0.3

    confidence_components.append(('temporal', temporal_score, 0.4))

    # 2. Publication volume consistency (30% weight)
    # More publications in early sustained period = higher confidence
    early_period_pubs = sum(1 for y in pub_years if sustained_start_year <= y < sustained_start_year + 5)
    if early_period_pubs >= 10:
        volume_score = 1.0
    elif early_period_pubs >= 5:
        volume_score = 0.8
    elif early_period_pubs >= 3:
        volume_score = 0.6
    else:
        volume_score = 0.4

    confidence_components.append(('volume', volume_score, 0.3))

    # 3. Topic consistency (30% weight)
    # Compare early papers' topics with overall author profile
    author_concepts = author.get('x_concepts', [])
    if author_concepts and len(works) >= 5:
        # Get top author concepts
        top_author_concepts = set(c.get('display_name', '').lower()
                                  for c in author_concepts[:10] if c.get('display_name'))

        # Get concepts from early works (first 5 years of sustained activity)
        early_works = [w for w in works
                      if w.get('publication_year') and
                      sustained_start_year <= w.get('publication_year') < sustained_start_year + 5]

        if early_works:
            early_concepts = set()
            for work in early_works[:10]:  # Sample first 10 early works
                work_concepts = work.get('concepts', [])
                for concept in work_concepts[:5]:  # Top 5 concepts per work
                    concept_name = concept.get('display_name', '').lower()
                    if concept_name:
                        early_concepts.add(concept_name)

            # Calculate overlap
            if early_concepts and top_author_concepts:
                overlap = len(early_concepts & top_author_concepts)
                topic_score = min(overlap / 5, 1.0)  # Normalize to 0-1
            else:
                topic_score = 0.5  # Neutral if no concept data
        else:
            topic_score = 0.5
    else:
        topic_score = 0.5  # Neutral if insufficient data

    confidence_components.append(('topic', topic_score, 0.3))

    # Calculate weighted confidence score
    total_confidence = sum(score * weight for _, score, weight in confidence_components)
    confidence_percentage = int(total_confidence * 100)

    # Determine confidence level
    if confidence_percentage >= 80:
        confidence_level = 'High'
    elif confidence_percentage >= 60:
        confidence_level = 'Medium'
    else:
        confidence_level = 'Low'

    # Generate notes
    notes = []
    if excluded_pubs > 0:
        notes.append(f"Excluded {excluded_pubs} publication(s) before sustained activity")
    if gap_before_sustained > 5:
        notes.append(f"{gap_before_sustained}-year gap before sustained activity")
    if excluded_pubs == 0 and gap_before_sustained == 0:
        notes.append("No outliers detected")

    return {
        'academic_age': academic_age,
        'confidence_score': confidence_percentage,
        'confidence_level': confidence_level,
        'first_pub_year': sustained_start_year,
        'earliest_pub_year': earliest_year,
        'excluded_pubs': excluded_pubs,
        'notes': '; '.join(notes) if notes else 'Based on sustained publication activity'
    }


def calculate_author_metrics(works: Optional[List[Dict]], h_index: int, works_count: int) -> Dict[str, Any]:
    """
    Calculate advanced metrics for an author based on their works.

    Args:
        works: List of work dictionaries from OpenAlex (or None if fetch failed)
        h_index: Author's h-index
        works_count: Total number of works

    Returns:
        Dictionary containing calculated metrics
    """
    if not works or len(works) == 0:
        return {
            'median_citations': 0,
            'mean_citations': 0,
            'top_10_concentration': 0,
            'recent_activity_rate': 0,
            'h_index_efficiency': 0
        }

    # Extract citation counts
    citation_counts = [work.get('cited_by_count', 0) for work in works]
    citation_counts_sorted = sorted(citation_counts, reverse=True)

    # 1. Median citations per work
    median_citations = statistics.median(citation_counts) if citation_counts else 0

    # 2. Mean citations per work
    mean_citations = statistics.mean(citation_counts) if citation_counts else 0

    # 3. Top 10% citation concentration
    total_citations = sum(citation_counts)
    if total_citations > 0:
        top_10_percent_count = max(1, len(works) // 10)
        top_10_percent_citations = sum(citation_counts_sorted[:top_10_percent_count])
        top_10_concentration = (top_10_percent_citations / total_citations) * 100
    else:
        top_10_concentration = 0

    # 4. Recent activity rate (last 5 years)
    current_year = datetime.now().year
    recent_works = [w for w in works if w.get('publication_year', 0) >= current_year - 5]
    recent_activity_rate = (len(recent_works) / len(works)) * 100 if works else 0

    # 5. h-index efficiency
    h_index_efficiency = (h_index / works_count) if works_count > 0 else 0

    return {
        'median_citations': round(median_citations, 1),
        'mean_citations': round(mean_citations, 1),
        'top_10_concentration': round(top_10_concentration, 1),
        'recent_activity_rate': round(recent_activity_rate, 1),
        'h_index_efficiency': round(h_index_efficiency, 3)
    }


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


def display_authors(authors_data: Dict) -> None:
    """
    Display authors search results.

    Args:
        authors_data: Dictionary containing author search results
    """
    if not authors_data or 'results' not in authors_data:
        st.warning("No results found.")
        return

    results = authors_data['results']
    st.success(f"Found {authors_data.get('meta', {}).get('count', 0)} total results")

    for author in results:
        with st.expander(f"👤 {author.get('display_name', 'Unknown Author')}"):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"**Name:** {author.get('display_name', 'N/A')}")

                # ORCID
                orcid = author.get('orcid')
                if orcid:
                    st.markdown(f"**ORCID:** [{orcid}]({orcid})")

                # Last known institution
                last_institution = author.get('last_known_institution')
                if last_institution:
                    inst_name = last_institution.get('display_name', 'Unknown')
                    st.markdown(f"**Institution:** {inst_name}")

                # OpenAlex ID
                openalex_id = author.get('id', '')
                if openalex_id:
                    st.markdown(f"[View in OpenAlex]({openalex_id})")

            with col2:
                # Works count
                works_count = author.get('works_count', 0)
                st.metric("Works", works_count)

                # Cited by count
                cited_by = author.get('cited_by_count', 0)
                st.metric("Citations", cited_by)

            with col3:
                # H-index
                h_index = author.get('summary_stats', {}).get('h_index', 0)
                st.metric("h-index", h_index)

                # i10-index
                i10_index = author.get('summary_stats', {}).get('i10_index', 0)
                st.metric("i10-index", i10_index)

            # Academic Age Section
            st.markdown("---")
            st.markdown("**📅 Academic Age Analysis**")

            with st.spinner("Calculating academic age..."):
                age_data = calculate_academic_age(author)

            if age_data['academic_age'] is not None:
                col_age1, col_age2, col_age3 = st.columns(3)

                with col_age1:
                    # Academic age with confidence indicator
                    confidence_color = {
                        'High': '🟢',
                        'Medium': '🟡',
                        'Low': '🔴',
                        'N/A': '⚪'
                    }.get(age_data['confidence_level'], '⚪')

                    st.metric(
                        "Academic Age",
                        f"{age_data['academic_age']} years",
                        help="Years since sustained publication activity began"
                    )

                with col_age2:
                    st.metric(
                        "Confidence",
                        f"{confidence_color} {age_data['confidence_score']}%",
                        help=f"Confidence level: {age_data['confidence_level']}"
                    )

                with col_age3:
                    st.metric(
                        "First Pub Year",
                        age_data['first_pub_year'],
                        help="Year of first sustained publication"
                    )

                # Additional details
                if age_data['excluded_pubs'] > 0 or age_data['earliest_pub_year'] != age_data['first_pub_year']:
                    st.caption(f"ℹ️ {age_data['notes']}")
                    if age_data['excluded_pubs'] > 0:
                        st.caption(f"Earliest publication: {age_data['earliest_pub_year']}")
            else:
                st.info(f"⚠️ {age_data['notes']}")

            # Advanced Metrics Section
            st.markdown("---")
            st.markdown("**📊 Advanced Publication Metrics**")

            with st.spinner("Calculating advanced metrics..."):
                author_id = author.get('id', '')
                if author_id and works_count > 0:
                    works = fetch_author_works(author_id)
                    metrics = calculate_author_metrics(works, h_index, works_count)

                    # Display advanced metrics in two rows
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Median Citations",
                            metrics['median_citations'],
                            help="Typical citation count per work (resistant to outliers)"
                        )
                    with col2:
                        st.metric(
                            "Mean Citations",
                            metrics['mean_citations'],
                            help="Average citations per work"
                        )
                    with col3:
                        st.metric(
                            "h-index Efficiency",
                            metrics['h_index_efficiency'],
                            help="h-index divided by total works (quality vs quantity)"
                        )

                    col4, col5, col6 = st.columns(3)
                    with col4:
                        st.metric(
                            "Top 10% Concentration",
                            f"{metrics['top_10_concentration']}%",
                            help="Percentage of citations from top 10% of papers"
                        )
                    with col5:
                        st.metric(
                            "Recent Activity",
                            f"{metrics['recent_activity_rate']}%",
                            help="Percentage of works published in last 5 years"
                        )
                    with col6:
                        # Empty column for symmetry
                        st.write("")
                else:
                    st.info("No works available to calculate advanced metrics.")

            # Concepts
            st.markdown("---")
            concepts = author.get('x_concepts', [])
            if concepts:
                st.markdown("**Research Areas:**")
                concept_names = [c.get('display_name', '') for c in concepts[:5]]
                st.markdown(", ".join(concept_names))


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="OpenAlex Search",
        page_icon="🔍",
        layout="wide"
    )

    st.title("🔍 OpenAlex Search")
    st.markdown("""
    Search for academic works and authors using the [OpenAlex API](https://docs.openalex.org/).
    OpenAlex is a free and open catalog of scholarly papers, authors, institutions, and more.
    """)

    # Create tabs
    tab1, tab2 = st.tabs(["📚 Search Works", "👤 Search Authors"])

    # Works Search Tab
    with tab1:
        st.header("Search for Academic Works")

        # Search input
        search_query = st.text_input(
            "Enter your search query:",
            placeholder="e.g., machine learning, climate change, quantum computing",
            help="Enter keywords to search for academic works",
            key="works_query"
        )

        # Search options
        col1, col2 = st.columns([3, 1])

        with col1:
            results_per_page = st.slider(
                "Results per page:",
                min_value=5,
                max_value=50,
                value=10,
                step=5,
                key="works_per_page"
            )

        with col2:
            page_number = st.number_input(
                "Page:",
                min_value=1,
                max_value=100,
                value=1,
                step=1,
                key="works_page"
            )

        # Search button
        if st.button("🔍 Search Works", type="primary", key="search_works"):
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

    # Authors Search Tab
    with tab2:
        st.header("Search for Authors")

        # Initialize session state for autocomplete
        if 'author_suggestions' not in st.session_state:
            st.session_state.author_suggestions = []
        if 'selected_author' not in st.session_state:
            st.session_state.selected_author = None

        st.info("💡 **Tip:** Type an author name and press Enter to see autocomplete suggestions, or enter a full name to search directly.")

        # Create columns for input and autocomplete button
        col_input, col_autocomplete = st.columns([3, 1])

        with col_input:
            # Text input for author name with autocomplete
            author_input = st.text_input(
                "Enter author name:",
                placeholder="e.g., John Smith",
                key="author_name_input",
                help="Type at least 2 characters and press Enter, or click 'Get Suggestions'"
            )

        with col_autocomplete:
            # Button to trigger autocomplete explicitly
            st.markdown("<br>", unsafe_allow_html=True)  # Align button with input
            autocomplete_btn = st.button(
                "🔍 Get Suggestions",
                key="autocomplete_button",
                help="Click to fetch author suggestions"
            )

        # Fetch autocomplete suggestions when button is clicked or when Enter is pressed
        should_fetch_suggestions = False

        # Check if button was clicked
        if autocomplete_btn and author_input and len(author_input) >= 2:
            should_fetch_suggestions = True
        # Check if text input changed (user pressed Enter)
        elif author_input and len(author_input) >= 2:
            if 'last_author_input' not in st.session_state or st.session_state.last_author_input != author_input:
                st.session_state.last_author_input = author_input
                should_fetch_suggestions = True

        # Fetch suggestions if needed
        if should_fetch_suggestions:
            with st.spinner("Fetching suggestions..."):
                st.session_state.author_suggestions = autocomplete_authors(author_input)
                st.session_state.selected_author = None

        # Display autocomplete suggestions if available
        if st.session_state.author_suggestions and len(st.session_state.author_suggestions) > 0:
            st.success(f"Found {len(st.session_state.author_suggestions)} suggestions")

            # Create a dictionary mapping display text to author data
            suggestions_dict = {}
            for author in st.session_state.author_suggestions:
                display_name = author.get('display_name', 'Unknown')
                hint = author.get('hint', '')
                works_count = author.get('works_count', 0)

                # Format the display text
                if hint:
                    display_text = f"{display_name} ({hint}) - {works_count} works"
                else:
                    display_text = f"{display_name} - {works_count} works"

                suggestions_dict[display_text] = author

            # Selectbox for choosing from suggestions
            selected_display = st.selectbox(
                "Select an author from suggestions:",
                options=[""] + list(suggestions_dict.keys()),
                format_func=lambda x: "-- Choose an author --" if x == "" else x,
                key="author_selectbox"
            )

            # Update selected author when user picks from selectbox
            if selected_display and selected_display != "":
                st.session_state.selected_author = suggestions_dict[selected_display]
                # Show selected author info
                selected = st.session_state.selected_author
                st.info(f"✓ Selected: **{selected.get('display_name')}** - Click 'Search Authors' below to view details")
        elif author_input and len(author_input) >= 2 and should_fetch_suggestions:
            st.warning("No suggestions found. Try a different name or search directly.")

        st.markdown("---")

        col1, col2 = st.columns([3, 1])
        with col1:
            authors_per_page = st.slider(
                "Results per page:",
                5, 50, 20,
                key="authors_per_page"
            )
        with col2:
            authors_search_btn = st.button(
                "🔍 Search Authors",
                type="primary",
                key="search_authors"
            )

        # Perform search when button is clicked
        if authors_search_btn:
            search_query = None

            # Use selected author's name if available, otherwise use text input
            if st.session_state.selected_author:
                search_query = st.session_state.selected_author.get('display_name')
            elif author_input:
                search_query = author_input

            if search_query:
                with st.spinner("Searching..."):
                    authors_data = search_openalex_authors(search_query, authors_per_page)
                    if authors_data:
                        display_authors(authors_data)
            else:
                st.warning("Please enter an author name or select from suggestions.")

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
