import os
import datetime
import re
import json
import requests
from typing import Generator, Dict, List, Any
import traceback

# Log file path
LOG_FILE = "../focus_log.txt"
# Flag to stop analysis
analysis_running = False

def ollama_stream_generator(prompt: str, model: str = "qwen2.5:7b") -> Generator[str, None, None]:
    """
    Ollama streaming response generator
    :param prompt: Input prompt text
    :param model: Model name to use
    :return: Iterator of generated text results
    """
    endpoint = "http://120.26.224.38:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,  # Enable streaming output
        "options": {
            "temperature": 0.7,  # Controls randomness (0-1)
            "num_predict": 4096  # Maximum number of generated tokens
        }
    }

    try:
        with requests.post(endpoint, json=payload, stream=True, timeout=30) as response:
            response.raise_for_status()  # Check for HTTP errors

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


def parse_focus_log(log_content: str, target_date: str = None) -> Dict[str, Any]:
    """
    Precisely parse the focus log and extract structured data

    Args:
        log_content (str): Log content
        target_date (str, optional): Target date (YYYY-MM-DD format), if provided only parse records of that date

    Returns:
        dict: Contains focus records, distraction records and other structured data
    """
    focus_entries = []
    distraction_entries = []

    # Log entry regular expression, matches formats like:
    # [2023-01-01 12:34:56] Output: {"status": "1. Focus"}
    # or
    # [2023-01-01 12:34:56] Output: {"status": "2. Distracted", "reason": "..."}
    entry_pattern = r'\[([\d]{4}-[\d]{2}-[\d]{2} [\d]{2}:[\d]{2}:[\d]{2})\] Output: ({.*?})(?=\n--|-\Z|$)'

    # Split log content into individual records
    records = log_content.split("--------------------------------------------------")

    # Process each record
    for record in records:
        if not record.strip():
            continue

        # Try to match timestamp and JSON data in the record
        matches = re.search(entry_pattern, record, re.DOTALL)
        if not matches:
            continue

        timestamp, json_data = matches.groups()

        # Extract date part
        date_str = timestamp.split()[0]

        # If target date specified and record does not match, skip
        if target_date and date_str != target_date:
            continue

        try:
            # Parse JSON data
            data = json.loads(json_data)
            entry = {
                "timestamp": timestamp,
                "time": timestamp.split()[1],  # Only keep the time part
                "status": data.get("status", ""),
                "is_focused": "1. Focus" in data.get("status", ""),
                "reason": data.get("reason", "") if "reason" in data else None
            }

            # Classify based on status
            if entry["is_focused"]:
                focus_entries.append(entry)
            else:
                distraction_entries.append(entry)

        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract information another way
            continue

    # Calculate analysis metrics
    total_entries = len(focus_entries) + len(distraction_entries)
    distraction_ratio = len(distraction_entries) / total_entries if total_entries > 0 else 0

    # Analyze distraction reasons
    distraction_reasons = {}
    for entry in distraction_entries:
        if entry["reason"]:
            if entry["reason"] in distraction_reasons:
                distraction_reasons[entry["reason"]] += 1
            else:
                distraction_reasons[entry["reason"]] = 1

    # Sort all records by time
    all_entries = focus_entries + distraction_entries
    all_entries.sort(key=lambda x: x["timestamp"])

    # Analyze time periods
    time_analysis = analyze_time_periods(all_entries)

    return {
        "date": target_date or "",
        "focus_entries": focus_entries,
        "distraction_entries": distraction_entries,
        "total_entries": total_entries,
        "focus_count": len(focus_entries),
        "distraction_count": len(distraction_entries),
        "distraction_ratio": distraction_ratio,
        "distraction_reasons": distraction_reasons,
        "timeline": all_entries,
        "time_analysis": time_analysis
    }


def analyze_time_periods(timeline: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Analyze time period data

    Args:
        timeline: List of records sorted by time

    Returns:
        dict: Time period analysis results
    """
    if not timeline:
        return {
            "high_focus_periods": "No data",
            "high_distraction_periods": "No data",
            "high_focus_hours": "No data",
            "high_distraction_hours": "No data"
        }

    # Divide a day into 3 periods
    periods = {
        "Morning (0-12)": {"focus": 0, "distraction": 0},
        "Afternoon (12-18)": {"focus": 0, "distraction": 0},
        "Evening (18-24)": {"focus": 0, "distraction": 0}
    }

    # Hourly statistics
    hours = {i: {"focus": 0, "distraction": 0} for i in range(24)}

    # Count focus/distraction records for each period and hour
    for entry in timeline:
        hour = int(entry["time"].split(":")[0])

        # Update hourly count
        if entry["is_focused"]:
            hours[hour]["focus"] += 1
        else:
            hours[hour]["distraction"] += 1

        # Update period count
        if 0 <= hour < 12:
            period = "Morning (0-12)"
        elif 12 <= hour < 18:
            period = "Afternoon (12-18)"
        else:
            period = "Evening (18-24)"

        if entry["is_focused"]:
            periods[period]["focus"] += 1
        else:
            periods[period]["distraction"] += 1

    # Calculate focus rate for each period
    period_focus_rates = {}
    for period, counts in periods.items():
        total = counts["focus"] + counts["distraction"]
        if total > 0:
            focus_rate = counts["focus"] / total
            period_focus_rates[period] = (focus_rate, total)

    # Calculate focus rate for each hour
    hour_focus_rates = {}
    for hour, counts in hours.items():
        total = counts["focus"] + counts["distraction"]
        if total > 0:
            focus_rate = counts["focus"] / total
            hour_focus_rates[hour] = (focus_rate, total)

    # Find periods with high and low focus rates
    high_focus_periods = []
    high_distraction_periods = []

    for period, (rate, count) in sorted(period_focus_rates.items(), key=lambda x: x[1][0], reverse=True):
        if rate >= 0.6 and count >= 2:
            high_focus_periods.append(f"{period} (Focus rate {rate * 100:.0f}%)")
        elif rate <= 0.4 and count >= 2:
            high_distraction_periods.append(f"{period} (Distraction rate {(1 - rate) * 100:.0f}%)")

    # Find hours with high and low focus rates
    high_focus_hours = []
    high_distraction_hours = []

    for hour, (rate, count) in sorted(hour_focus_rates.items(), key=lambda x: x[1][0], reverse=True):
        if rate >= 0.7 and count >= 2:
            high_focus_hours.append(f"{hour}:00-{hour + 1}:00 (Focus rate {rate * 100:.0f}%)")
        elif rate <= 0.3 and count >= 2:
            high_distraction_hours.append(f"{hour}:00-{hour + 1}:00 (Distraction rate {(1 - rate) * 100:.0f}%)")

    # Take top 3 results
    high_focus_periods = high_focus_periods[:3]
    high_distraction_periods = high_distraction_periods[:3]
    high_focus_hours = high_focus_hours[:3]
    high_distraction_hours = high_distraction_hours[:3]

    return {
        "high_focus_periods": ", ".join(high_focus_periods) if high_focus_periods else "No obvious high focus period",
        "high_distraction_periods": ", ".join(high_distraction_periods) if high_distraction_periods else "No obvious high distraction period",
        "high_focus_hours": ", ".join(high_focus_hours) if high_focus_hours else "No obvious high focus hour",
        "high_distraction_hours": ", ".join(high_distraction_hours) if high_distraction_hours else "No obvious high distraction hour"
    }


def format_distraction_reasons(reasons: Dict[str, int]) -> str:
    """
    Format distraction reason analysis

    Args:
        reasons: Distraction reason statistics dictionary

    Returns:
        str: Formatted distraction reason text
    """
    if not reasons:
        return "No distraction records or reasons found"

    result = ""
    for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
        result += f"- {reason} (Occurred {count} times)\n"

    return result


def get_dates_from_log():
    """
    Extract all dates from the log file and return a sorted list of dates
    """
    if not os.path.exists(LOG_FILE):
        return []

    dates = set()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        # More accurately match dates in format [YYYY-MM-DD HH:MM:SS]
        date_patterns = re.findall(r'\[(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2}\]', content)
        for date in date_patterns:
            dates.add(date)

    # Sort dates
    return sorted(list(dates))


def filter_logs_by_date(date_str: str) -> str:
    """
    Filter log content by specified date with precise matching

    Args:
        date_str (str): Date string in format YYYY-MM-DD

    Returns:
        str: Log content for the specified date
    """
    if not os.path.exists(LOG_FILE):
        return ""

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Split log into records by separator
    records = content.split("--------------------------------------------------")

    # More accurately filter records containing the specified date
    date_pattern = r'\[' + date_str + r' \d{2}:\d{2}:\d{2}\]'
    filtered_records = []

    for record in records:
        if re.search(date_pattern, record):
            filtered_records.append(record)

    # Recombine filtered records
    result = ""
    if filtered_records:
        result = "--------------------------------------------------".join(filtered_records)
        # Ensure each record is followed by the separator
        if not result.endswith("--------------------------------------------------"):
            result += "--------------------------------------------------"

    return result


def user_select_date():
    """
    Let user choose the date to analyze: today, specific date, or exit

    Returns:
        str: Selected date string in YYYY-MM-DD format, or empty string if exit
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    available_dates = get_dates_from_log()

    print("\n" + "=" * 40)
    print("       📊 Focus Log Analysis 📊")
    print("=" * 40)
    print(f"1. Analyze today's log ({today})")
    print("2. Choose historical date")
    print("0. Exit program")
    print("-" * 40)

    choice = input("Enter option number: ")

    if choice == "1":
        # Check if there is a log for today
        if today not in available_dates:
            print(f"\n⚠️ Warning: No log records for today ({today})")
            return today if input("Continue analyzing anyway? (y/n): ").lower() == 'y' else ""
        return today
    elif choice == "2":
        if not available_dates:
            print("❌ No available date records found in the log")
            return ""

        print("\n📅 Available dates:")
        # Display dates in groups, max 4 per line
        for i in range(0, len(available_dates), 4):
            row = available_dates[i:i + 4]
            formatted_row = "  ".join([f"{j + 1 + i}. {date}" for j, date in enumerate(row)])
            print(formatted_row)
        try:
            date_choice = int(input("\nEnter date number: "))
            if 1 <= date_choice <= len(available_dates):
                return available_dates[date_choice - 1]
            else:
                print("❌ Invalid choice")
                return ""
        except ValueError:
            print("❌ Please enter a valid number")
            return ""
    elif choice == "0":
        print("👋 Exiting program")
        return ""
    else:
        print("❌ Invalid choice")
        return ""


def analyze_daily_focus(date_str: str, headless=False):
    """
    Analyze the focus log for the specified date using the improved parser

    Args:
        date_str (str): Date string in YYYY-MM-DD format
        headless (bool): Whether to run in headless mode (without console output)
    """
    if not os.path.exists(LOG_FILE):
        if not headless:
            print(f"❌ Error: Log file {LOG_FILE} not found")
        return None

    if not headless:
        print(f"\n🔍 Analyzing focus records for {date_str}...")

    # Read and parse log
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        log_content = f.read()

    # Use the improved parser to get structured data
    parsed_data = parse_focus_log(log_content, target_date=date_str)

    if parsed_data["total_entries"] == 0:
        if not headless:
            print(f"❌ No log records found for {date_str}")
        return None

    # Get raw log text for completeness check
    raw_daily_logs = filter_logs_by_date(date_str)

    # Build a more detailed and structured prompt
    prompt = f"""
[Role]: You are a professional focus analysis assistant, good at extracting insights from log data and generating practical improvement suggestions.

[Data]: The following is the analysis result of the user's focus monitoring log for {date_str}:

1. Basic statistics:
   - Total records: {parsed_data["total_entries"]}
   - Focused records: {parsed_data["focus_count"]}
   - Distracted records: {parsed_data["distraction_count"]}
   - Distraction ratio: {parsed_data["distraction_ratio"] * 100:.1f}%

2. Time analysis:
   - High focus periods: {parsed_data["time_analysis"]["high_focus_periods"]}
   - High distraction periods: {parsed_data["time_analysis"]["high_distraction_periods"]}
   - High focus hours: {parsed_data["time_analysis"]["high_focus_hours"]}
   - High distraction hours: {parsed_data["time_analysis"]["high_distraction_hours"]}

3. Distraction reason analysis:
{format_distraction_reasons(parsed_data["distraction_reasons"])}

4. Raw log records:
{raw_daily_logs}

[Analysis task]:
Please, based on the above data analysis, generate a structured daily focus report, which should include:

1. Basic statistics: Summarize and evaluate focus status based on the provided statistics.
2. Time patterns: Analyze changes in focus level throughout the day, identifying best and worst time periods.
3. Distraction reasons: Analyze the patterns and frequencies of distraction reasons, identifying the most critical interfering factors.
4. Focus performance: Evaluate the user's overall focus performance for the day, and whether a good focus state was achieved.
5. Specific suggestions: Provide 3-5 concrete and feasible improvement suggestions based on the identified distraction patterns and reasons.

[Output format]:
Please use the following text format to return the analysis result:

# Daily Focus Report
Date: {date_str}

## Basic Statistics
- Number of focus records: {parsed_data["focus_count"]}
- Number of distraction records: {parsed_data["distraction_count"]}
- Distraction ratio: {parsed_data["distraction_ratio"] * 100:.1f}%

## Time Pattern Analysis
- High focus periods: [Fill based on data analysis]
- High distraction periods: [Fill based on data analysis]

## Distraction Reason Analysis
[Analyze based on provided distraction reason data]

## Performance Evaluation
[Overall evaluation of focus performance for the day]

## Improvement Suggestions
- [Area 1]: [Concrete suggestion] → Expected effect: [Expected effect]
- [Area 2]: [Concrete suggestion] → Expected effect: [Expected effect]
- [Area 3]: [Concrete suggestion] → Expected effect: [Expected effect]

[Notes]:
- Strictly base your analysis on the provided data, do not add content that does not exist
- Suggestions must be specific and actionable, avoid generalities
- The analysis should be in-depth, finding patterns rather than just repeating data
"""

    try:
        model_name = "Qwen2.5:7b"  # Or use other available models

        if not headless:
            print(f"\n===== Generating Focus Analysis Report for {date_str} =====\n")

        # Use streaming generation for instant feedback
        output = ""
        for text_chunk in ollama_stream_generator(prompt, model=model_name):
            if not headless:
                print(text_chunk, end="", flush=True)
            output += text_chunk
            
            # Check if analysis needs to be stopped
            global analysis_running
            if not analysis_running:
                if not headless:
                    print("\n\n❌ Analysis stopped by user")
                return None

        # Save report to file
        daily_report_dir = "../FocusReports/daily_report"
        os.makedirs(daily_report_dir, exist_ok=True)
        daily_report_file = os.path.join(daily_report_dir, f"FocusReport_{date_str}.txt")

        with open(daily_report_file, "w", encoding="utf-8") as f:
            f.write(output)

        if not headless:
            print(f"\n\n✅ Report saved to: {daily_report_file}")
            
        return daily_report_file

    except Exception as e:
        if not headless:
            print(f"\n❌ Analysis failed: {str(e)}")
            traceback.print_exc()
        return None


def main():
    """Main program entry"""
    print("\n" + "*" * 50)
    print("        🧠 Focus Monitoring Analysis System 🧠")
    print("*" * 50)
    print("\nThis system can analyze your focus log and provide detailed reports and improvement suggestions.")

    while True:
        date = user_select_date()
        if not date:
            break

        analyze_daily_focus(date)

        print("\n" + "-" * 40)
        choice = input("Press Enter to continue, input 'q' to exit: ")
        if choice.lower() == 'q':
            print("👋 Thank you for using the Focus Monitoring Analysis System!")
            break


if __name__ == "__main__":
    main()

# Added function: start or stop daily analysis
def start_stop_daily_analysis(start=True, date_str=None):
    """
    Start or stop daily analysis
    
    Args:
        start (bool): True to start analysis, False to stop analysis
        date_str (str): Date string to analyze, defaults to today
    
    Returns:
        dict: Operation result
    """
    global analysis_running
    
    if start:
        if analysis_running:
            return {"success": False, "message": "Analysis is already running"}
        
        # Set running state
        analysis_running = True
        
        # Default to today's date
        if date_str is None:
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")
            
        # Check date format
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return {"success": False, "message": "Invalid date format, please use YYYY-MM-DD format"}
        
        # Execute analysis asynchronously (in a real application, this should use threads or async tasks)
        # Simplified here, directly calling the analysis function
        result = analyze_daily_focus(date_str, headless=True)
        
        # Reset running state after completion
        analysis_running = False
        
        if result:
            return {"success": True, "message": f"Daily analysis completed: {date_str}", "report_path": result}
        else:
            return {"success": False, "message": f"Daily analysis failed: {date_str}"}
    else:
        # Stop analysis
        if not analysis_running:
            return {"success": False, "message": "No analysis is currently running"}
        
        analysis_running = False
        return {"success": True, "message": "Daily analysis stopped"}
