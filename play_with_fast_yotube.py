import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime
import csv

# Constants and configuration
SHEET_ID = '1jESaEV_iK5GSuO2WDV8RTcDzP42WmDIE4dAIei7yYFU'
RANGE_NAME = 'Sheet1'
SERVICE_ACCOUNT_FILE = 'caption-comparison-3dd6dfcad088.json'
num_ids = 580

# Initialize Google Sheets API
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()


# 读取视频 URL 映射
def load_video_urls(csv_file):
    video_urls = []
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            video_urls.append(row['Video URL'])
    return video_urls

# 加载视频 URL 列表
video_urls = load_video_urls('random_sample_videos.csv')

def get_video_url(id):
    # 根据 id 获取视频 URL
    if id < 0 or id >= len(video_urls):
        return None
    return video_urls[id]


import streamlit as st
from datetime import datetime

# Ensure to set up your Google Sheets API and credentials
# RANGE_NAME and SHEET_ID should be defined here or imported
# Also, define `sheet` which represents the Google Sheets API client.

def save_score_to_sheet(id, score, reviewer_name, reason):
    row_index = id + 10624  # Assuming data starts from the third row, id is a 0-based index

    score_cell = f"{RANGE_NAME}!E{row_index}"
    current_scores = sheet.values().get(spreadsheetId=SHEET_ID, range=score_cell).execute().get('values', [['']])[0][0]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Process existing scores
    all_scores = current_scores.split('\n')
    user_scores = {}
    for s in all_scores:
        if ':' in s:
            name, rest = s.split(':', 1)
            user_scores[name.strip()] = rest.strip()
    
    # Update with the new score
    user_scores[reviewer_name] = f"{score} at {timestamp}"
    
    # Convert back to the final string for storage
    final_scores = '\n'.join([f"{name}: {s}" for name, s in user_scores.items()])
    score_value = [{'range': score_cell, 'values': [[final_scores]]}]
    body = {'valueInputOption': 'USER_ENTERED', 'data': score_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=body).execute()

    # Update the rating reason
    reason_cell = f"G{row_index}"
    current_reasons = sheet.values().get(spreadsheetId=SHEET_ID, range=reason_cell).execute().get('values', [['']])[0][0]
    # Process existing reasons
    all_reasons = current_reasons.split('\n')
    user_reasons = {}
    for r in all_reasons:
        if ':' in r:
            name, rest = r.split(':', 1)
            user_reasons[name.strip()] = rest.strip()

    # Update with the new reason
    user_reasons[reviewer_name] = f"{reason}, at {timestamp}"

    # Convert back to the final string for storage
    final_reasons = '\n'.join([f"{name}: {r}" for name, r in user_reasons.items()])
    reason_value = [{'range': reason_cell, 'values': [[final_reasons]]}]
    reason_body = {'valueInputOption': 'USER_ENTERED', 'data': reason_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=reason_body).execute()

    # Update the history
    history_cell = f"F{row_index}"
    current_history = sheet.values().get(spreadsheetId=SHEET_ID, range=history_cell).execute().get('values', [['']])[0][0]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_history = f"{current_history}\n{reviewer_name}: {score} at {timestamp}".strip()
    history_value = [{'range': history_cell, 'values': [[new_history]]}]
    history_body = {'valueInputOption': 'USER_ENTERED', 'data': history_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=history_body).execute()

    # Calculate the average score based on the latest scores
    total_score = 0
    for s in user_scores.values():
        score_value = float(s.split(' ')[0])
        total_score += score_value
    average_score = total_score / len(user_scores)

    num_raters = len(user_scores)
    
    # Update the average score in column C
    result_cell = f"{RANGE_NAME}!D{row_index}"
    result_value = [{'range': result_cell, 'values': [[f"{average_score:.2f}\nNumber of raters: {num_raters}"]]}]
    result_body = {'valueInputOption': 'USER_ENTERED', 'data': result_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=result_body).execute()

def submit(id, score, reviewer_name, reason):
    # Check if the reviewer name or reason is missing and display a prominent error message
    if not reviewer_name:
        st.error("Error: You must enter your name to rate this video. Please enter your name below.")
        return False  # Return None to stop the execution of the function here
    # if not reason:
    #     st.error("Error: You must provide a reason for your rating. Please enter your reason below.")
    #     return False  # Return None to stop the execution of the function here
    save_score_to_sheet(id, score, reviewer_name, reason)
    return True
    
# 读取视频 URL 映射
def load_video_urls(csv_file):
    video_urls = []
    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            video_urls.append(row['Video URL'])
    return video_urls

# 加载视频 URL 列表
video_urls = load_video_urls('random_sample_videos.csv')

def next_video():
    if "video_index" in st.session_state:
        if st.session_state["video_index"] < len(st.session_state["video_urls"]) - 1:
            st.session_state["video_index"] += 1
        else:
            st.warning('This is the last video.')

def previous_video():
    if "video_index" in st.session_state:
        if st.session_state["video_index"] > 0:
            st.session_state["video_index"] -= 1
        else:
            st.warning('This is the first video.')

def main():
    st.title("Data Rating Tool")
    st.write("Please review the YouTube video URL to decide whether it should remain in our dataset.")

    if "video_urls" not in st.session_state:
        st.session_state["video_urls"] = video_urls
        st.session_state["video_index"] = 0

    # 添加一个下拉菜单来选择视频ID
    ids = list(range(len(video_urls)))  # 确保下拉菜单的范围与视频URL列表的长度一致
    id_dropdown = st.selectbox("Choose Video ID", ids, index=st.session_state["video_index"])

    # 更新视频索引
    st.session_state["video_index"] = id_dropdown
    video_index = st.session_state["video_index"]
    video_url = video_urls[video_index]

    # Display video URL
    if video_url:
        st.write(f"Video URL: {video_url}")

    # Navigation and progress bar
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.button("Previous Video", on_click=previous_video)
    with col2:
        st.button("Next Video", on_click=next_video)
    with col3:
        progress = video_index / len(video_urls)
        st.progress(progress)

    # Rating interface
    score_input = st.slider("Rate the video (1: Terrible, 3: Pass, 5: High quality)", 1, 5, value=3)
    reviewer_name_input = st.text_input("Your Name", placeholder="Enter your name...")
    reason_input = st.text_area("Rating Reason (NOT MANDATORY) ", placeholder="Enter your reason for rating...")

    if st.button("Submit Rating"):
        result = submit(video_index, score_input, reviewer_name_input, reason_input)
        if result:
            st.success("Rating and reason saved successfully.")

if __name__ == "__main__":
    main()
