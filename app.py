import streamlit as st
import requests
import base64
import json

st.title("Google Search API with Data for SEO")

keywords = st.text_area("Keywords (semicolon-separated)", "bora bora; maldives; hawaii")
locations = st.text_area("Locations (semicolon-separated)", "21133; 21135; 21136; 21137; 21138; 21139; 21140")  # Example location codes
google_domain = st.text_input("Google Domain", "google.com")
language_code = st.text_input("Language Code", "en")
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

        fetched_json_responses = results

        # Extract and display item_types and ai_overview
        for task_result in results.get('tasks', []):
            result = task_result.get('result', [{}])[0] if task_result.get('result') else {}
            item_types = result.get('item_types', [])
            st.write(f"Item Types for Task ID {task_result.get('id')}: {item_types}")

            # Check if "ai_overview" is in item_types
            if "ai_overview" in item_types:
                items = result.get('items', [])
                for item in items:
                    if item.get('type') == 'ai_overview':
                        if debug:
                            st.write(f"Full AI Overview Item: {json.dumps(item, indent=4)}")
                        # Extract relevant fields
                        ai_overview_content = {
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "source": item.get("source"),
                            "text": item.get("text")
                        }
                        # Convert to string and display
                        ai_overview_str = json.dumps(ai_overview_content, indent=4)
                        st.write(f"AI Overview for Task ID {task_result.get('id')}: {ai_overview_str}")
                        break  # Stop after finding the first ai_overview

    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
    except (IndexError, KeyError, TypeError) as e:
        st.error(f"Unexpected response structure: {e}")
        if debug:
            st.write("### Error Details")
            st.write(f"Response: {results}")

    # Provide a link to download the full JSON response
    if download_json and fetched_json_responses:
        json_data = json.dumps(fetched_json_responses, indent=4)
        st.download_button(
            label="Download Fetched JSON Responses",
            data=json_data,
            file_name='fetched_json_responses.json',
            mime='application/json',
        )
