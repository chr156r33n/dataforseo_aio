import streamlit as st
import requests
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import base64
import tempfile

def generate_auth_header(email, api_password):
    auth_str = f"{email}:{api_password}"
    auth_bytes = auth_str.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    return f"Basic {auth_base64}"

def extract_ai_overview_content(ai_overview):
    if ai_overview is None:
        return None
    content = {
        "title": ai_overview.get("title"),
        "text": ai_overview.get("text"),
        "references": []
    }
    for ref in ai_overview.get("references", []):
        content["references"].append({
            "source": ref.get("source"),
            "domain": ref.get("domain"),
            "url": ref.get("url"),
            "title": ref.get("title"),
            "text": ref.get("text")
        })
    return content

def save_json_to_tempfile(data):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(temp_file.name, 'w') as f:
        json.dump(data, f, indent=4)
    return temp_file.name

st.title("Google Search API with DataForSEO")

keywords = st.text_area("Keywords (semicolon-separated)", "bora bora; skin flooding trend; longevity research")
locations = st.text_area("Location Codes (semicolon-separated)", "2840; 21167; 1012820")  # Example location codes
language_code = st.text_input("Language Code", "en")
device = st.text_input("Device", "desktop")
os = st.text_input("OS", "windows")
email = st.text_input("Email", "youremail@address.com")
api_password = st.text_input("API Password", "api_key_here", type="password")
num_calls = st.number_input("Number of API Calls per Keyword", min_value=1, max_value=10, value=1)

if st.button("Search"):
    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    keyword_list = [keyword.strip() for keyword in keywords.split(";")]
    location_code_list = [location.strip() for location in locations.split(";")]

    combined_similarity_data = []
    raw_html_files = []

    for keyword in keyword_list:
        st.write(f"## Results for Keyword: {keyword}")
        all_results = []
        ai_overview_items = []
        no_ai_overview_indices = []
        for i in range(num_calls):
            payload = json.dumps([{
                "keyword": keyword,
                "location_code": int(location_code_list[i % len(location_code_list)]),  # Rotate through location codes
                "language_code": language_code,
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
                
                # Navigate to tasks[0].result[0].items
                items = results.get('tasks', [])[0].get('result', [])[0].get('items', [])
                ai_overview = next((item for item in items if item.get('type') == 'ai_overview'), None)
                
                raw_html_file = results.get('search_metadata', {}).get('raw_html_file')
                if raw_html_file:
                    raw_html_files.append({
                        "keyword": keyword,
                        "location_code": location_code_list[i % len(location_code_list)],
                        "raw_html_file": raw_html_file
                    })
                if ai_overview:
                    # Extract and clean ai_overview content
                    cleaned_content = extract_ai_overview_content(ai_overview)
                    if cleaned_content:
                        ai_overview_items.append({
                            "keyword": keyword,
                            "iteration": i + 1,
                            "content": cleaned_content
                        })
                else:
                    no_ai_overview_indices.append(i + 1)

                # Save JSON result to temporary file and create download link
                json_filename = save_json_to_tempfile(results)
                with open(json_filename, 'rb') as f:
                    st.download_button(
                        label=f"Download JSON Result for {keyword} (Call {i + 1})",
                        data=f,
                        file_name=f'{keyword.replace(" ", "_")}_result_{i + 1}.json',
                        mime='application/json',
                    )
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {e}")
                break

        if ai_overview_items:
            st.write("### AI Overview Items")
            for idx, ai_overview in enumerate(ai_overview_items):
                st.write(f"**AI Overview Item {idx + 1} (Keyword: {ai_overview['keyword']}, Iteration: {ai_overview['iteration']}):** {json.dumps(ai_overview['content'], indent=4)}\n")

            # Compute similarity
            ai_overview_texts = [item["content"]["text"] for item in ai_overview_items if item["content"]["text"]]
            if ai_overview_texts:
                try:
                    vectorizer = TfidfVectorizer().fit_transform(ai_overview_texts)
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
                except ValueError as e:
                    st.error(f"Error computing similarity: {e}")
            else:
                st.write("No valid AI overview texts found for similarity computation.")
        else:
            st.write("No AI overview items found in the results.")

        if no_ai_overview_indices:
            st.write("### Requests with No AI Overview")
            st.write(f"No AI overview found in the following requests: {no_ai_overview_indices}")

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
