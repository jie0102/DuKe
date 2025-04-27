import sys
import json
import requests
import os
from typing import Generator
from analysis.weekly_prompt import parse_specific_files, generate_summary_text,generate_prompt
from datetime import datetime, timedelta
import glob

# Flag to stop analysis
analysis_running = False

def ollama_stream_generator(prompt: str, model: str = "Qwen2.5:7b") -> Generator[str, None, None]:
    """
    Ollama streaming response generator
    :param prompt: Input prompt text
    :param model: Model name to use
    :return: An iterator of generated text results
    """
    endpoint = "http://120.26.224.38:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,  # Enable streaming output
        "options": {
            "temperature": 0.7,  # Controls randomness (0-1)
            "num_predict": 32768  # Maximum number of generated tokens
        }
    }

    try:
        with requests.post(endpoint, json=payload, stream=True, timeout=30) as response:
            response.raise_for_status()  # Check HTTP errors

            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        yield chunk.get("response", "")
                    except json.JSONDecodeError:
                        print(" | [JSON parsing error] ", end="", flush=True)
                    except Exception as e:
                        print(f" | [Data parsing error: {str(e)}] ", end="", flush=True)

    except requests.exceptions.RequestException as e:
        print(f"\nRequest failed: {str(e)}")
    except Exception as e:
        print(f"\nUnknown error: {str(e)}")


def get_week_range(weeks_ago=0):
    """
    Get the date range for a specific week
    :param weeks_ago: How many weeks ago (0 means current week)
    :return: Start and end date of the week
    """
    today = datetime.now().date()
    # Find Monday of this week
    start_of_this_week = today - timedelta(days=today.weekday())
    # Calculate start and end date for the specified week
    start_date = start_of_this_week - timedelta(weeks=weeks_ago)
    end_date = start_date + timedelta(days=6)
    return start_date, end_date


def get_weekly_files(weeks_ago=0):
    """
    Get the list of daily report files for a specific week
    :param weeks_ago: How many weeks ago (0 means current week)
    :return: List of file paths
    """
    start_date, end_date = get_week_range(weeks_ago)
    date_range = []

    # Generate all dates in the range
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    # Find matching files
    matching_files = []
    for date_str in date_range:
        pattern = f"../FocusReports/daily_report/FocusReport_{date_str}.txt"
        files = glob.glob(pattern)
        matching_files.extend(files)

    return matching_files, start_date, end_date


def get_prompt(files_list):
    """
    Call the function in weekly_prompt to get the generated prompt.
    """
    log_summary = parse_specific_files(files_list)
    summary_text = generate_summary_text(log_summary)
    final_prompt = generate_prompt(summary_text)
    return final_prompt


def analyze_prompt_with_ollama(prompt, headless=False):
    """
    Analyze the prompt using the remote API.
    """
    global analysis_running
    model = "Qwen2.5:7b"  # Replace with the appropriate model name
    full_response = []

    if not headless:
        print("Analyzing data...")

    try:
        for text_chunk in ollama_stream_generator(prompt, model):
            if not headless:
                print(text_chunk, end="", flush=True)  # Real-time output
            full_response.append(text_chunk)
            
            # Check if analysis needs to be stopped
            if not analysis_running:
                if not headless:
                    print("\n\n❌ Analysis stopped by user")
                return None

        return ''.join(full_response)
    except Exception as e:
        if not headless:
            print(f"Error calling the model: {e}")
        return f"Error during analysis: {str(e)}"


def save_to_weekly_log(analysis_result, start_date, end_date):
    """
    Save the analysis result to a weekly report file under weekly_report directory, filename includes date range
    """
    # Ensure directory exists
    os.makedirs("../FocusReports/weekly_report", exist_ok=True)

    # Create filename
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    file_name = f"../FocusReports/weekly_report/WeeklyReport_{start_str}_to_{end_str}.md"

    # Add header and time info
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"# Weekly Focus Report ({start_str} to {end_str})\n\n"
    header += f"*Generated at: {current_time}*\n\n"
    header += f"---\n\n"

    # Write to file
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(header + analysis_result)

    print(f"\nAnalysis result saved to {file_name}")
    return file_name


def display_menu():
    """
    Display menu and get user selection
    """
    print("\n==== Focus Weekly Report Generation System ====")
    print("Please choose the type of weekly report to generate:")
    print("1. This week's report")
    print("2. Last week's report")
    print("3. Report from two weeks ago")
    print("4. Report from three weeks ago")
    print("5. Report from four weeks ago")
    print("0. Exit program")

    choice = input("Enter option number: ")
    return choice


# Added function: start or stop weekly analysis
def start_stop_weekly_analysis(start=True, weeks_ago=0):
    """
    Start or stop weekly analysis
    
    Args:
        start (bool): True to start analysis, False to stop analysis
        weeks_ago (int): How many weeks ago, 0 means current week
    
    Returns:
        dict: Operation result
    """
    global analysis_running
    
    if start:
        if analysis_running:
            return {"success": False, "message": "Analysis is already running"}
        
        # Set running state
        analysis_running = True
        
        try:
            # Get files and analyze
            files, start_date, end_date = get_weekly_files(weeks_ago)
            
            if not files:
                analysis_running = False
                period_str = "current week" if weeks_ago == 0 else f"{weeks_ago} weeks ago"
                return {
                    "success": False, 
                    "message": f"No daily report files found for {period_str} ({start_date} to {end_date})"
                }
            
            # Generate prompt
            prompt = get_prompt(files)
            
            # Analyze and generate report
            analysis = analyze_prompt_with_ollama(prompt, headless=True)
            
            # If analysis was interrupted, return interruption info
            if analysis is None:
                return {"success": False, "message": "Analysis was interrupted by user"}
            
            # Save report
            report_path = save_to_weekly_log(analysis, start_date, end_date)
            
            # Reset state after completion
            analysis_running = False
            
            return {
                "success": True,
                "message": f"Weekly analysis completed: {start_date} to {end_date}",
                "report_path": report_path
            }
            
        except Exception as e:
            analysis_running = False
            return {"success": False, "message": f"Weekly analysis failed: {str(e)}"}
    else:
        # Stop analysis
        if not analysis_running:
            return {"success": False, "message": "No analysis is currently running"}
        
        analysis_running = False
        return {"success": True, "message": "Weekly analysis stopped"}


if __name__ == '__main__':
    while True:
        choice = display_menu()

        if choice == "0":
            print("Program exited.")
            sys.exit(0)

        try:
            weeks_ago = int(choice) - 1
            if weeks_ago < 0 or weeks_ago > 4:
                print("Invalid option, please choose again.")
                continue

            files, start_date, end_date = get_weekly_files(weeks_ago)

            if not files:
                period_str = "This week" if weeks_ago == 0 else f"{weeks_ago} week(s) ago"
                print(f"No daily report files found for {period_str} ({start_date} to {end_date})!")
                continue

            print(f"\nFound {len(files)} daily report files:")
            for file in files:
                print(f" - {os.path.basename(file)}")

            confirm = input("\nGenerate weekly report? (y/n): ")
            if confirm.lower() != 'y':
                continue
            # Generate prompt
            prompt = get_prompt(files)

            # Analyze prompt with remote API
            analysis = analyze_prompt_with_ollama(prompt)

            # Save analysis result
            save_path = save_to_weekly_log(analysis, start_date, end_date)


        except ValueError:
            print("Please enter a valid number!")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
