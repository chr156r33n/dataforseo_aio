import streamlit as st
import requests
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import base64

def generate_auth_header(email, api_password):
    auth_str = f"{email}:{api_password}"
    auth_bytes = auth_str.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    return f"Basic {auth_base64}"

st.title("Google Search API with DataForSEO")

keywords = st.text_area("Keywords (semicolon-separated)", "bora bora; skin flooding trend; longevity research")
locations = st.text_area("Location Codes (semicolon-separated)", "2840; 21167; 1012820")  # Example location codes
language_codes = st.text_area("Language Codes (semicolon-separated)", "21138; 21139; 21140; 21141; 21142")  # Example language codes
device = st.text_input("Device", "desktop")
os = st.text_input("OS", "windows")
email = st.text_input("Email", "youremail@address.com")
api_password = st.text_input("API Password", "api_key_here", type="password")
num_calls = st.number_input("Number of API Calls per Keyword", min_value=1, max_value=10, value=1)

if st.button("Search"):
    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    keyword_list = [keyword.strip() for keyword in keywords.split(";")]
    location_code_list = [location.strip() for location in locations.split(";")]
    language_code_list = [language_code.strip() for language_code in language_codes.split(";")]

    combined_similarity_data = []
    raw_html_files = []
    json_results = []

    for keyword in keyword_list:
        st.write(f"## Results for Keyword: {keyword}")
        all_results = []
        answer_boxes = []
        no_answer_box_indices = []
        for i in range(num_calls):
            payload = json.dumps([{
                "keyword": keyword,
                "location_code": int(location_code_list[i % len(location_code_list)]),  # Rotate through location codes
                "language_code": language_code_list[i % len(language_code_list)],  # Rotate through language codes
                "device": device,
                "os": os
            }])

            headers = {
                "Content-Type": "application/json",
                "Authorization": generate_auth_header(email, api_password)
            }

            try:
                response = requests.post(url, headers=headers, data=payload)
                response.raise_for_status()  # Raise an error for bad status codes
                results = response.json()
                all_results.append(results)
                json_results.append({
                    "keyword": keyword,
                    "location_code": location_code_list[i % len(location_code_list)],
                    "results": results
                })
                answer_box = results.get('answer_box')
                raw_html_file = results.get('search_metadata', {}).get('raw_html_file')
                if raw_html_file:
                    raw_html_files.append({
                        "keyword": keyword,
                        "location_code": location_code_list[i % len(location_code_list)],
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
                    "location_code": location_code_list[row_idx % len(location_code_list)],
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
            st.write(f"Keyword: {entry['keyword']}, Location Code: {entry['location_code']}, [Raw HTML File]({entry['raw_html_file']})")

        df_raw_html = pd.DataFrame(raw_html_files)
        csv_raw_html = df_raw_html.to_csv(index=False)
        st.download_button(
            label="Download Raw HTML Files as CSV",
            data=csv_raw_html,
            file_name='raw_html_files.csv',
            mime='text/csv',
        )

    # Export JSON results
    if json_results:
        json_data = json.dumps(json_results, indent=4)
        st.download_button(
            label="Download JSON Results",
            data=json_data,
            file_name='json_results.json',
            mime='application/json',
        )
