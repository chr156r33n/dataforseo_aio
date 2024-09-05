import streamlit as st
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import base64
import json

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
download_json = st.checkbox("Download Fetched JSON", False)

if st.button("Search"):
    # Encode email and password in Base64
    credentials = f"{email}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    keyword_list = [keyword.strip() for keyword in keywords.split(";")]
    location_list = [location.strip() for location in locations.split(";")]

    combined_similarity_data = []
    fetched_json_responses = []

    for keyword in keyword_list:
        if debug:
            st.write(f"## Processing Keyword: {keyword}")
        all_results = []
        ai_overviews = []
        no_ai_overview_indices = []
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
                if debug:
                    st.write(f"Response: {results}")

                all_results.append(results)
                fetched_json_responses.append(results)
                task_result = results.get('tasks', [{}])[0].get('result', [{}])[0] if results.get('tasks') else {}
                items = task_result.get('items', [])
                ai_overview = None
                for item in items:
                    if item.get('type') == 'ai_overview':
                        ai_overview = item.get('text')
                        break

                if ai_overview:
                    # Convert ai_overview to string
                    ai_overviews.append(str(ai_overview))
                else:
                    no_ai_overview_indices.append(i + 1)
            except requests.exceptions.RequestException as e:
                st.error(f"Error: {e}")
                break
            except (IndexError, KeyError, TypeError) as e:
                st.error(f"Unexpected response structure: {e}")
                if debug:
                    st.write(f"Response: {results}")
                break

        if ai_overviews:
            st.write("### AI Overviews")
            for idx, ai_overview in enumerate(ai_overviews):
                st.write(f"**AI Overview {idx + 1}:** {ai_overview}\n")

            # Compute similarity
            vectorizer = TfidfVectorizer().fit_transform(ai_overviews)
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
            st.write("No AI overviews found in the results.")

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

    # Export fetched JSON responses
    if download_json and fetched_json_responses:
        json_data = json.dumps(fetched_json_responses, indent=4)
        st.download_button(
            label="Download Fetched JSON Responses",
            data=json_data,
            file_name='fetched_json_responses.json',
            mime='application/json',
        )
