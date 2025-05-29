from fastapi import FastAPI, File, UploadFile, HTTPException
import pandas as pd
import os
from io import BytesIO
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    print("in request")
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file.")
    
    contents = await file.read()
    df = pd.read_excel(BytesIO(contents))
    
    report = generate_text_report(df)
    return {"report": report}

def generate_text_report(df):
    # Prepare the Azure OpenAI API endpoint
    url = f"{os.environ.get('OPENAI_AZURE_ENDPOINT')}openai/deployments/gpt-4-turbo-2024-04-09/chat/completions?api-version={os.environ.get('OPENAI_AZURE_API_VERSION')}"
    print(url)
    # Prepare the headers with the API key
    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENAI_AZURE_API_KEY')}",
        "Content-Type": "application/json"
    }

    # Create the prompt for the AI model
    prompt = f"""
    Generate a summary report for the following dataset:
    {df.head(10).to_string(index=False)}
    Provide insights on trends, anomalies, and overall patterns.
    """

    data = {
        "messages": [
            {"role": "system", "content": "You are a data analyst."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    # Send the request to the Azure OpenAI endpoint
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        result = response.json()
        return result["choices"][0]["message"]["content"]
    else:
        print(f"Error: {response.status_code} - {response.text}")
        raise HTTPException(status_code=response.status_code, detail=response.text)

# Streamlit Web Interface
def main():
    st.title("Excel Report Generator")
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xls", "xlsx"])
    
    if uploaded_file is not None:
        print("in main")
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post("http://127.0.0.1:8000/upload/", files=files)
        
        if response.status_code == 200:
            st.subheader("Generated Report:")
            st.markdown(response.json()["report"])
        else:
            st.error(f"Error generating report: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
