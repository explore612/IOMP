from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import json
import os
import requests
import uuid
from datetime import datetime
import re
import string

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize the SentenceTransformer model
model = SentenceTransformer('multi-qa-mpnet-base-dot-v1')

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'dev_user',
    'password': 'secure_password',
    'database': 'project_similarity'
}

# Helper function to generate embedding
def generate_embedding(text):
    return model.encode(text).tolist()

# Helper function to calculate cosine similarity
def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Helper function to categorize similarity
def categorize_similarity(similarity_score):
    if similarity_score >= 0.8:
        return "High"
    elif similarity_score >= 0.5:
        return "Medium"
    else:
        return "Low"


@app.route('/api/load_data', methods=['POST'])
def load_data():
    """Load original data from a CSV file into the database."""
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()

    try:
        # Read data from a CSV file (update the path to your CSV file)
        df = pd.read_csv('data/dataset.csv', encoding='ISO-8859-1')

        # Insert the data into the Project table
        insert_query = "INSERT INTO project_iomp (id, title, abstract) VALUES (%s, %s, %s)"
        data = df[['id', 'title', 'abstract']].values.tolist()
        
        # Clear the existing data (optional)
        cursor.execute("TRUNCATE TABLE Project")
        
        # Insert the new data
        cursor.executemany(insert_query, data)
        connection.commit()
        return jsonify({"message": "Original data loaded successfully"}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/api/generate_embeddings', methods=['POST'])
def generate_embeddings():
    """Generate embeddings for all projects in the database."""
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, title, abstract FROM project_iomp")
        projects = cursor.fetchall()

        for project in projects:
            combined_text = clean_text(project['title']) + " " + clean_text(project['abstract'])
            embedding = generate_embedding(combined_text)
            embedding_json = json.dumps(embedding)
            cursor.execute("UPDATE project_iomp SET embedding = %s WHERE id = %s", (embedding_json, project['id']))

        connection.commit()
        return jsonify({"message": "Embeddings generated successfully"}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/api/find_similar_projects', methods=['POST'])
def find_similar_projects():
    """Find top 10 similar projects based on user input, categorize similarity, and check for gibberish input."""
    user_text = request.json.get('text')
    user_abstract = request.json.get('abstract')
    print('step1')

    if not user_text or not user_abstract:
        return jsonify({"error": "Both title and abstract input are required"}), 400

    # Generate embedding for the combined user input (title + abstract)
    combined_input = user_text + " " + user_abstract
    user_embedding = generate_embedding(combined_input)

    # Connect to the database and fetch all project embeddings
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT id, title, abstract, embedding FROM project_iomp")
    projects = cursor.fetchall()

    similarities = []
    max_similarity = 0

    for project in projects:
        project_embedding = json.loads(project['embedding'])
        similarity = cosine_similarity(user_embedding, project_embedding)

        # Update max similarity score
        max_similarity = max(max_similarity, similarity)

        # Check if both title and abstract are identical
        is_identical = (
            user_text.strip().lower() == project['title'].strip().lower() and
            user_abstract.strip().lower() == project['abstract'].strip().lower()
        )
        similarity_category = categorize_similarity(similarity)

        similarities.append({
           "id": project['id'],
           "title": project['title'],
           "abstract": project['abstract'],
           "similarity": similarity,
           "similarity_category": "Identical" if is_identical else similarity_category,
            "warning": "Highly identical project" if is_identical else None
        })

        #  # Add warning if similarity is greater than 0.9
        # warning = None
        # if is_identical:
        #     warning = "Highly identical project"
        # elif similarity > 0.9:
        #     warning = "This project is highly similar to your input"

        # similarities.append({
        #     "id": project['id'],
        #     "title": project['title'],
        #     "abstract": project['abstract'],
        #     "similarity": similarity,
        #     "similarity_category": "Identical" if is_identical else similarity_category,
        #     "warning": warning
        # })

    print('step 2')
     # Filter out projects with similarity scores less than 0.5
    similarities = [item for item in similarities if item['similarity'] >= 0.3]

    print('step 3')

    # Sort projects by similarity score in descending order and place identical entries at the top
    similarities = sorted(similarities, key=lambda x: (-int(x['similarity_category'] == "Identical"), -x['similarity']))[:3]

    print('step 4')
    search_guid = check_with_llm(similarities, combined_input)
    print('step 5')
    search_results = get_matching_data(search_guid)
    cursor.close()
    connection.close()
    print('step 6')
    return jsonify(search_results), 200

def get_matching_data(search_guid):
    print(f'Getting matching data for {search_guid}')
    # SQL query
    query = """
    SELECT 
        project_iomp.id,
        project_iomp.title,
        project_iomp.abstract,
        user_session.search_guid,
        user_session.cosine_similarity matching_score,
        user_session.matching_comments
    FROM user_session
    INNER JOIN project_iomp ON user_session.matched_project_id = project_iomp.id
    WHERE user_session.search_guid = %s
    """

    try:
        # Establish the database connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Execute the query with the provided search GUID
        cursor.execute(query, (search_guid,))

        # Fetch all the results
        results = cursor.fetchall()

        # Return the results as a list of dictionaries
        return results

    except mysql.connector.Error as e:
        print(f"Error fetching data: {e}")
        return []

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def check_with_llm(projects, user_abstract):
    results = []
    guid = str(uuid.uuid4())

    for idx, project in enumerate(projects):
        print(f"Processing Project {idx + 1}/{len(projects)}")
        # Call the interact_with_llm method for each project abstract
        comparison_result = interact_with_llm(project, user_abstract)
        store_matching_info_to_db(guid, project, comparison_result, user_abstract)

    return guid

def store_matching_info_to_db(guid, project, result_data, user_abstract):
    print(f'Storing the matching informaiton')

     # Extract information from result_data
    matched_project_id = project['id']
    cosine_similarity = int(project.get("similarity", 0) * 100)
    # matching_score = int(result_data.get("similarity_score", 0))
    # matching_comments = result_data.get("comments", "")
    matching_comments = result_data

    try:
        # Establish the database connection
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # SQL insert query
        insert_query = """
        INSERT INTO user_session (search_guid, user_abstract, matched_project_id, cosine_similarity, matching_comments, created_dt)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        # Prepare the data for insertion
        created_dt = datetime.now()
        data = (guid, user_abstract, matched_project_id, cosine_similarity, matching_comments, created_dt)

        # print(f'Executing the Insert with {guid} :: {user_abstract} ::{matched_project_id} :: {cosine_similarity}:: {json.dumps(matching_comments)} :: {created_dt}')

        # Execute the insert query
        cursor.execute(insert_query, data)

        # Commit the transaction
        connection.commit()

        return "Record successfully inserted into user_session table."

    except mysql.connector.Error as e:
        return f"Error inserting record: {e}"

    except Exception as e:
        # Catch any unexpected errors
        print(f"An unexpected error occurred: {e}")
        return f"Unexpected error: {e}"

    finally:
        # Close the database connection
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def interact_with_llm(project, user_abstract):
    """
    Interacts with the LLaMA API, sends a prompt, and extracts JSON response.
    Returns an empty dictionary if any error occurs.
    """
    project_abstract = project['abstract']
    prompt = generate_prompt(project_abstract, user_abstract, project['similarity'])
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "temperature": 0.1,
        "max_tokens": 256,
        "stop": None,
        "stream": False
    }

    try:
        # Send POST request to the LLaMA API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        # Extract the 'response' field from the API response
        data = response.json()
        llm_response = data.get('response', '')

        # Extract JSON data from the response text
        # completion = extract_json_from_response(llm_response)

        return llm_response

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}

    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from API response: {e}")
        return {}

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}

def extract_json_from_response(response_text):
    """
    Extracts JSON data from the given response text.
    Returns an empty dictionary if no valid JSON is found.
    """

    try:
        # Regular expression to find the JSON object in the response
        json_pattern = r"\{[\s\S]*\}"
        match = re.search(json_pattern, response_text)

        if match:
            # Extract the JSON string
            json_str = match.group(0).strip()

            # Check if the extracted string is non-empty
            if not json_str:
                print("Extracted JSON string is empty.")
                return {}

            # Parse the JSON string into a Python dictionary
            json_data = json.loads(json_str)
            return json_data

        else:
            print("No JSON found in the response.")
            print(response_text)
            return {}

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Failed to decode JSON: {e}")
        return {}

    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}


def generate_prompt(project_abstract, user_abstract, cosine_similarity):
    # Base system prompt logic with adjustments for LLaMA 3.2
    if cosine_similarity > 0.90:
        focus_instruction = "Focus primarily on the **similarities** between the abstracts, but include key differences."
    elif 0.70 < cosine_similarity <= 0.90:
        focus_instruction = "Provide a slightly **similarity-focused** view, while still discussing key differences."
    elif 0.40 < cosine_similarity <= 0.70:
        focus_instruction = "Provide a **balanced view**, discussing both similarities and differences equally."
    else:  # cosine_similarity <= 0.40
        focus_instruction = "Focus primarily on the **differences** between the abstracts, but include key similarities."

    # System prompt with specific format instructions
    system_prompt = f"""
    You are an academic reviewer analyzing two project abstracts. Your task is to compare them and output the results in the following structure:

    ### Similarities:
    (List the key similarities here in bullet points)

    ### Differences:
    (List the key differences here in bullet points)

    Analysis focus: {focus_instruction}

    Ensure that in your response, you refer the abstracts as existing project and proposed project.

    Abstracts for comparison are provided below:
    """

    # Format the abstracts
    formatted_project_abstract = f"#### Existing Project Abstract:\n{project_abstract.strip()}\n"
    formatted_user_abstract = f"#### Proposed Project Abstract:\n{user_abstract.strip()}\n"

    # Combine the system prompt with the abstracts
    combined_prompt = (
        f"{system_prompt}\n\n"
        f"{formatted_project_abstract}\n"
        f"{formatted_user_abstract}"
    )

    return combined_prompt

def clean_text(text: str) -> str:
    """
    Cleans the input text by:
    1. Converting to lowercase
    2. Removing punctuation and special characters
    3. Stripping extra whitespace
    """
    if not isinstance(text, str):
        return ""  # Return an empty string if the input is not a string

    # 1. Convert text to lowercase
    text = text.lower()

    # 2. Remove punctuation and special characters
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)

    # 3. Strip extra whitespace (tabs, newlines, multiple spaces)
    text = re.sub(r"\s+", " ", text).strip()

    return text


if __name__ == '__main__':
    app.run(port=5001)