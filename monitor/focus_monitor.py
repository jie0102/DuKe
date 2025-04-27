import os
import time
import re
import json
import mss
import mss.tools
import pytesseract
from PIL import Image
import win32gui
import requests
import tkinter as tk
from tkinter import messagebox
from typing import List, Dict, Generator

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Log file path
LOG_FILE = "../focus_log.txt"
# Default whitelist and blacklist
WHITE_LIST = []
BLACK_LIST = []
# Flag to stop monitoring
stop_monitoring = False

# ---------------------------
# Initialize log file (create if not exists)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("Focus Monitoring Log\n")
        f.write("=" * 50 + "\n\n")

def log_json_output(timestamp, json_output):
    """
    Record user's focus status log: time + model JSON output
    """
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] Output: {json_output}\n")
        log.write("-" * 50 + "\n\n")

# ---------------------------
# Screenshot section: using mss
def capture_screenshot():
    """Capture the current screen and save to a specified folder"""
    SCREENSHOT_FOLDER = "screenshots"
    try:
        if not os.path.exists(SCREENSHOT_FOLDER):
            os.makedirs(SCREENSHOT_FOLDER)
        screenshot_path = os.path.join(SCREENSHOT_FOLDER, f"screenshot_{int(time.time())}.png")
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return None

# ---------------------------
# OCR recognition function (using pytesseract)
def ocr_screen_content(screenshot_path):
    try:
        img = Image.open(screenshot_path)
        text = pytesseract.image_to_string(img, lang='chi_sim')
        return text.strip()
    except Exception as e:
        print(f"OCR recognition error: {e}")
        return "OCR recognition failed"

# ---------------------------
# Get currently open window titles
def get_running_processes():
    """Get the titles of currently running application windows"""
    apps = []
    ignored_apps = ['Program Manager', 'Microsoft Text Input Application']

    def get_windows(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if win32gui.IsWindowVisible(hwnd) and title and title not in ignored_apps:
            apps.append(title)

    win32gui.EnumWindows(get_windows, None)
    return apps

# ---------------------------
# Intervention: pop-up reminder (show reason from JSON output if available)
def intervene(reason=""):
    """
    When user is detected as distracted, use tkinter to pop up a reminder window,
    displaying the distraction reason if provided by the model.
    """
    root = tk.Tk()
    root.withdraw()  # Hide main window
    message = "Distraction detected"
    if reason:
        message += f": {reason}"
    message += ", please adjust your state to stay focused!"
    messagebox.showwarning("Intervention Reminder", message)
    root.destroy()

# ---------------------------
# Get whitelist and blacklist input from user
def get_user_input_for_whitelist_and_blacklist():
    """
    Let user enter whitelist and blacklist applications.
    """
    global WHITE_LIST, BLACK_LIST
    white_list_input = input("Enter the main applications needed for your current task (comma separated): ")
    WHITE_LIST = [app.strip() for app in white_list_input.split(",")]
    black_list_input = input("Enter applications that may distract you (comma separated): ")
    BLACK_LIST = [app.strip() for app in black_list_input.split(",")]
    print(f"Whitelist set: {WHITE_LIST}")
    print(f"Blacklist set: {BLACK_LIST}")

# ----------------------
# Add function to clean up screenshots
def cleanup_screenshots():
    """
    When the number of screenshots exceeds 100, delete the oldest screenshot files.
    """
    SCREENSHOT_FOLDER = "screenshots"
    MAX_SCREENSHOTS = 100

    if not os.path.exists(SCREENSHOT_FOLDER):
        return

    # Get all screenshot files and their creation times
    screenshots = []
    for filename in os.listdir(SCREENSHOT_FOLDER):
        if filename.startswith("screenshot_") and filename.endswith(".png"):
            filepath = os.path.join(SCREENSHOT_FOLDER, filename)
            create_time = os.path.getctime(filepath)
            screenshots.append((filepath, create_time))

    # Delete oldest files if exceeding the limit
    if len(screenshots) > MAX_SCREENSHOTS:
        screenshots.sort(key=lambda x: x[1])
        files_to_delete = len(screenshots) - MAX_SCREENSHOTS
        print(f"Screenshot file count reached {len(screenshots)}, cleaning up {files_to_delete} oldest files...")
        for i in range(files_to_delete):
            try:
                os.remove(screenshots[i][0])
                print(f"Deleted old screenshot: {os.path.basename(screenshots[i][0])}")
            except Exception as e:
                print(f"Failed to delete screenshot: {e}")

# ---------------------------
# Remote large model API call function
def chat_with_remote_model(messages: List[Dict[str, str]], model: str = "Qwen2.5:7b") -> str:
    """
    Call remote API for large language model chat
    :param messages: List of chat messages
    :param model: Model name
    :return: Model response content
    """
    endpoint = "http://120.26.224.38:11434/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.7
        }
    }
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()  # Check HTTP error

        result = response.json()
        return result.get("message", {}).get("content", "")

    except Exception as e:
        print(f"Remote API call failed: {str(e)}")
        return f"Error: {str(e)}"

# ---------------------------
# Main program
def run_monitor(preset_goal=None, preset_white_list=None, preset_black_list=None, headless=False):
    global WHITE_LIST, BLACK_LIST, stop_monitoring
    
    # Reset stop flag
    stop_monitoring = False
    
    # Use preset values or get user input
    if preset_white_list is not None:
        WHITE_LIST = preset_white_list
    if preset_black_list is not None:
        BLACK_LIST = preset_black_list
    
    if preset_goal is None or preset_white_list is None or preset_black_list is None:
        # Only get user input when no preset values
        if preset_white_list is None and preset_black_list is None:
            get_user_input_for_whitelist_and_blacklist()
        user_goal = preset_goal if preset_goal else input("Enter your current work goal: ")
    else:
        user_goal = preset_goal
    
    model_name = "Qwen2.5:7b"  # Use model available on remote server
    
    if not headless:
        print("\nFocus monitoring started. The program will check your focus status every 5 minutes...")
        print("Press Ctrl+C to exit at any time\n")

    try:
        while not stop_monitoring:
            # Clean up screenshot files
            cleanup_screenshots()

            # Screenshot and OCR recognition
            screenshot_path = capture_screenshot()
            if not screenshot_path:
                print("Screenshot failed, retrying in 5 minutes...")
                time.sleep(300)
                continue

            screen_content = ocr_screen_content(screenshot_path)
            running_processes = get_running_processes()
            running_processes_str = ", ".join(running_processes)

            # Construct model input
            messages = [
                {"role": "user", "content": (
                    f"Work goal: {user_goal}\n"
                    f"Screen recognized content: {screen_content}\n"
                    f"Running background processes: {running_processes_str}\n"
                    f"Whitelist set: {WHITE_LIST}\n"
                    f"Blacklist set: {BLACK_LIST}\n"
                )},
                {"role": "system", "content": (
                    """You are an intelligent and empathetic focus supervision assistant. Your task is to reasonably analyze the user's work status, and only give reminders when truly necessary. Please judge the user's status according to the following rules:
1. Focused: Meets the following condition:
   - Screen content is basically related to the work goal

2. Distracted: Only judged as distracted if ALL the following conditions are met:
   - Using applications obviously unrelated to work
   - Using applications in the blacklist
   - Screen content is completely unrelated to the work goal

Judgment principles:
- Use a lenient standard to avoid excessive intervention
- Allow reasonable work switching and short breaks
- Only remind when clear distraction is detected
- Prioritize user experience and avoid frequent interruptions

Notes:
- Application names may have case/locale differences, please match flexibly
- Whitelisted apps are considered essential for work and not counted as distractions
- Do not over-interpret background elements like desktop icons

Output format (output ONLY one of the following JSON formats):
- Focused state:
  {"status": "1. Focused"}
- Clear distracted state:
  {"status": "2. Distracted", "reason": "<specific and friendly description of distraction reason>"}
Ensure your output only contains the JSON above, do not add any other content."""
                )}
            ]

            try:
                print("Analyzing your focus status...")
                # Call remote API model
                output = chat_with_remote_model(messages, model_name)

                # Extract reasoning and final output
                reasoning_pattern = r"<think>(.*?)</think>"
                final_output_pattern = r"</think>\s*(.+)"
                reasoning_match = re.search(reasoning_pattern, output, re.DOTALL)
                if reasoning_match:
                    reasoning_text = reasoning_match.group(1).strip()
                else:
                    reasoning_text = ""
                final_output_match = re.search(final_output_pattern, output, re.DOTALL)
                if final_output_match:
                    final_output_text = final_output_match.group(1).strip()
                else:
                    final_output_text = output.strip()
                # Try to parse final output as JSON
                try:
                    json_output = json.loads(final_output_text)
                except Exception as e:
                    print(f"Failed to parse JSON output: {e}")
                    print("Raw output:", final_output_text)
                    print("Will retry in 5 minutes...")
                    time.sleep(300)
                    continue
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                log_json_output(timestamp, final_output_text)
                status = json_output.get("status", "")
                if status == "1. Focused":
                    # No intervention if focused
                    print(f"[{timestamp}] Result: You are currently focused!")
                elif status == "2. Distracted":
                    reason = json_output.get("reason", "")
                    print(f"[{timestamp}] Result: Distracted - {reason}")
                    intervene(reason)
                else:
                    print(f"[{timestamp}] Unable to determine status, please check model output.")
            except Exception as e:
                print(f"Model call error: {e}")

            # Wait 5 minutes
            print("\nNext check will be in 5 minutes...\n")
            time.sleep(300)

    except KeyboardInterrupt:
        print("\nProgram stopped. Thank you for using DuKe:the Focus Monitoring Tool!")
