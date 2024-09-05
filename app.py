import streamlit as st
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import base64

st.title("Google Search API with Data for SEO")

keywords = st.text_area("Keywords (semicolon-separated)", "bora bora; maldives; hawaii")
locations = st.text_area("Locations (semicolon-separated)", "Austin, Texas, United States; New York, New York, United States; San Francisco, California, United States")
google_domain = st.text_input("Google Domain", "google.com")
gl = st.text_input("GL", "us")
hl = st.text_input("HL", "en")
no_cache = st.checkbox("No Cache", True)
email = st.text_input("Email", "your_email@example.com")
password = st.text_input("Password", "your_password", type="password")
num_calls = st.number_input("Number of API Calls per Keyword", min_value=1, max_value=10, value=1)
debug = st.checkbox("Enable Debugging", False)

if st.button("Search"):
    # Encode email and password in Base64
    credentials = f"{email}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    keyword_list = [keyword.strip() for keyword in keywords.split(";")]
    location_list = [location.strip() for location in locations.split(";")]

    combined_similarity_data = []
    raw_html_files = []

    for keyword in keyword_list:
        if debug:
            st.write(f"## Processing Keyword: {keyword}")
        all_results = []
        answer_boxes = []
        no_answer_box_indices = []
        for i in range(num_calls):
            params = {
                "keyword": keyword,
                "location_name": location_list[i % len(location_list)],  # Rotate through location values
                "google_domain": google_domain,
                "gl": gl,
                "hl": hl,
                "device": "desktop",
                "os": "windows"
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Basic {encoded_credentials}"
            }

            if debug:
                st.write(f"### API Call {i + 1} for Keyword: {keyword}")
                st.write(f"Params: {params}")

            try:
                response = requests.post(url, json=params, headers=headers)
                response.raise_for_status()  # Raise an error for bad status codes
                results = response.json()
                all_results.append(results)
                answer_box = results.get('tasks', [{}])[0].get('result', [{}])[0].get('answer_box')
                raw_html_file = results.get('tasks', [{}])[0].get('result', [{}])[0].get('search_metadata', {}).get('raw_html_file')
                if raw_html_file:
                    raw_html_files.append({
                        "keyword": keyword,
                        "location": location_list[i % len(location_list)],
                        "raw_html_file": raw_html_file
                    })
                if answer_box:
                    # Convert answer_box to string
                    answer_boxes.append(str(answer_box))
                else:
                    no_answer_box_indices.append(i + 1)
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {e}")
                break

        if answer_boxes:
            st.write("### Answer Boxes")
            for idx, answer_box in enumerate(answer_boxes):
                st.write(f"**Answer Box {idx + 1}:** {answer_box}\n")

            # Compute similarity
            vectorizer = TfidfVectorizer().fit_transform(answer_boxes)
            vectors = vectorizer.toarray()
            cosine_matrix = cosine_similarity(vectors)

            st.write("### Similarity Matrix")
            st.write(cosine_matrix)

            # Combine similarity data
            for row_idx, row in enumerate(cosine_matrix):
                combined_similarity_data.append({
                    "keyword": keyword,
                    "location": location_list[row_idx % len(location_list)],
                    **{f"similarity_{col_idx + 1}": value for col_idx, value in enumerate(row)}
                })
        else:
            st.write("No answer boxes found in the results.")

        if no_answer_box_indices:
            st.write("### Requests with No Answer Box")
            st.write(f"No answer box found in the following requests: {no_answer_box_indices}")

    # Export combined similarity matrix
    if combined_similarity_data:
        df_similarity = pd.DataFrame(combined_similarity_data)
        csv_similarity = df_similarity.to_csv(index=False)
        st.download_button(
            label="Download Combined Similarity Matrix as CSV",
            data=csv_similarity,
            file_name='combined_similarity_matrix.csv',
            mime='text/csv',
        )

    # Display and export raw HTML files
    if raw_html_files:
        st.write("### Raw HTML Files")
        for entry in raw_html_files:
            st.write(f"Keyword: {entry['keyword']}, Location: {entry['location']}, [Raw HTML File]({entry['raw_html_file']})")

        df_raw_html = pd.DataFrame(raw_html_files)
        csv_raw_html = df_raw_html.to_csv(index=False)
        st.download_button(
            label="Download Raw HTML Files as CSV",
            data=csv_raw_html,
            file_name='raw_html_files.csv',
            mime='text/csv',
        )
