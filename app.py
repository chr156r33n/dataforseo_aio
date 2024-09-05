import streamlit as st
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import base64
import json

st.title("Google Search API with Data for SEO")

keywords = st.text_area("Keywords (semicolon-separated)", "bora bora; maldives; hawaii")
locations = st.text_area("Locations (semicolon-separated)", "2840; 21167; 1012820")  # Example location codes
google_domain = st.text_input("Google Domain", "google.com")
language_code = st.text_input("Language Code", "en")
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
    location_list = [int(location.strip()) for location in locations.split(";")]

    combined_similarity_data = []
    fetched_json_responses = []
    ai_overviews = []
    no_ai_overview_indices = []

    tasks = []
    for keyword in keyword_list:
        for i in range(num_calls):
            task = {
                "keyword": keyword,
                "location_code": location_list[i % len(location_list)],  # Rotate through location values
                "language_code": language_code,
                "google_domain": google_domain,
                "device": "desktop",
                "os": "windows"
            }
            tasks.append(task)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {encoded_credentials}"
    }

    payload = json.dumps(tasks)  # Convert tasks list to JSON array

    if debug:
        st.write(f"### Sending {len(tasks)} tasks to Data for SEO API")
        st.write(f"Payload: {payload}")

    try:
        response = requests.post(url, data=payload, headers=headers)  # Send as JSON array
        response.raise_for_status()  # Raise an error for bad status codes
        results = response.json()
        if debug:
            st.write("### Response Summary")
            st.write(f"Status Code: {response.status_code}")
            st.write(f"Number of Tasks: {len(results.get('tasks', []))}")

        fetched_json_responses.append(results)

        for task_result in results.get('tasks', []):
            result = task_result.get('result', [{}])[0] if task_result.get('result') else {}
            items = result.get('items', [])
            if debug:
                st.write(f"Items for Task ID {task_result.get('id')}: {json.dumps(items, indent=4)}")
            ai_overview = None
            for item in items:
                if item.get('type') == 'ai_overview':
                    ai_overview = item.get('text')
                    break  # Stop processing further items once ai_overview is found

            if ai_overview:
                # Convert ai_overview to string
                ai_overviews.append(str(ai_overview))
            else:
                no_ai_overview_indices.append(task_result.get('id'))

    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
    except (IndexError, KeyError, TypeError) as e:
        st.error(f"Unexpected response structure: {e}")
        if debug:
            st.write("### Error Details")
            st.write(f"Response: {results}")

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
