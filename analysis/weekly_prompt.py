import re
import os
import glob
from datetime import datetime, timedelta

def parse_log_file(directory_path):
    """
    Parse all log files in the directory
    """
    file_paths = glob.glob(os.path.join(directory_path, "*.txt"))
    return parse_specific_files(file_paths)

def parse_specific_files(file_paths):
    """
    Parse the given list of log files
    :param file_paths: List of log file paths
    :return: Summarized log data
    """
    summary = {"focus": 0, "distracted": 0, "distraction_reasons": [], "daily_data": {}}

    for file_path in file_paths:
        try:
            # Extract date from filename
            filename = os.path.basename(file_path)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            date = date_match.group(1) if date_match else "Unknown Date"

            if date not in summary["daily_data"]:
                summary["daily_data"][date] = {"focus": 0, "distracted": 0, "distraction_reasons": []}

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                process_text_content(content, summary, date)

        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")

    return summary

def get_files_for_date_range(start_date, end_date, directory_path):
    """
    Get log files within the specified date range
    :param start_date: Start date (YYYY-MM-DD)
    :param end_date: End date (YYYY-MM-DD)
    :param directory_path: Log file directory
    :return: List of file paths
    """
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    if end_date_obj < start_date_obj:
        start_date_obj, end_date_obj = end_date_obj, start_date_obj

    selected_files = []
    current_date = start_date_obj

    while current_date <= end_date_obj:
        date_str = current_date.strftime("%Y-%m-%d")
        date_files = glob.glob(os.path.join(directory_path, f"*{date_str}*.txt"))
        selected_files.extend(date_files)
        current_date += timedelta(days=1)

    return selected_files

def process_text_content(content, summary, date):
    """
    Process text-based records
    """
    daily_report_match = re.search(r'# Daily Focus Report', content)

    if daily_report_match:
        # Process structured daily focus report
        focused_count_match = re.search(r'Number of focus records:\s*(\d+)', content)
        distracted_count_match = re.search(r'Number of distraction records:\s*(\d+)', content)

        if focused_count_match:
            focused_count = int(focused_count_match.group(1))
            summary["focus"] += focused_count
            summary["daily_data"][date]["focus"] += focused_count

        if distracted_count_match:
            distracted_count = int(distracted_count_match.group(1))
            summary["distracted"] += distracted_count
            summary["daily_data"][date]["distracted"] += distracted_count

        # Extract distraction reasons
        causes_section = re.search(r'## Distraction Reason Analysis\n(.*?)(?:\n##|\Z)', content, re.DOTALL)
        if causes_section:
            causes_text = causes_section.group(1)
            causes = re.findall(r'- (.*?)\s*\(Occurred \d+ times\):\s*(.*?)(?:\n-|\Z)', causes_text, re.DOTALL)
            for cause, examples in causes:
                cause = cause.strip()
                summary["distraction_reasons"].append(cause)
                summary["daily_data"][date]["distraction_reasons"].append(cause)
    else:
        # Split log records by separator
        records = content.split("--------------------------------------------------")

        for rec in records:
            state_match = re.search(r'Status:\s*(focus|distracted)', rec)
            if state_match:
                state = state_match.group(1)
                summary[state] += 1
                summary["daily_data"][date][state] += 1

                # If distracted, extract reason
                if state == "distracted":
                    reason_match = re.search(r'Reason(?: Explanation)?:\s*(.+)', rec, re.DOTALL)
                    if reason_match:
                        reason = reason_match.group(1).strip()
                        summary["distraction_reasons"].append(reason)
                        summary["daily_data"][date]["distraction_reasons"].append(reason)

def generate_summary_text(summary):
    """
    Generate summary text based on statistics
    """
    total_events = summary['focus'] + summary['distracted']
    text = f"In the recorded logs, there were {total_events} monitoring events in total, including {summary['focus']} focused events and {summary['distracted']} distracted events."

    text += "\n\nData summary by date:"
    for date, data in summary.get("daily_data", {}).items():
        daily_total = data['focus'] + data['distracted']
        text += f"\n- {date}: {daily_total} events in total, {data['focus']} focused, {data['distracted']} distracted"

    if summary["distraction_reasons"]:
        reason_counts = {}
        for reason in summary["distraction_reasons"]:
            if reason in reason_counts:
                reason_counts[reason] += 1
            else:
                reason_counts[reason] = 1

        sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
        top_reasons = sorted_reasons[:5]

        text += "\n\nMain distraction reasons include:"
        for reason, count in top_reasons:
            text += f"\n- {reason} (Occurred {count} times)"

    return text

def generate_prompt(summary_text):
    """
    Embed statistics summary into Prompt template.
    """
    prompt_part1 = f"""
[Role]: You are a health assistant. Your task is to comprehensively analyze the user's weekly focus log and generate a weekly summary report. The log records daily focus and distraction status (including timestamps, status, and distraction reasons, etc).

[Context]:
Below is a summary of data automatically counted from your logs over the past period:
[Historical Log Data]:
{summary_text}

[Task]:
Based on the above [Historical Log Data], please analyze the user's long-term work status in depth and answer the following:
1. Count daily focus and distraction events this week;
2. Analyze the time periods and frequency of distraction events;
3. Summarize common distraction reasons and identify main interference factors;
4. Evaluate the effectiveness of interventions (such as popup reminders) this week;
5. Propose improvement suggestions and optimization strategies to help the user stay focused in the future.

"""
    prompt_part2 = f"""
[Output Format]:

# Weekly Focus Summary Report

## Daily Data Statistics
- YYYY-MM-DD: focused [number] times, distracted [number] times
- YYYY-MM-DD: focused [number] times, distracted [number] times
(include statistics for all dates in the week)

## Distraction Pattern Analysis
[Analysis of the time periods and frequency of distraction events]

## Common Distraction Reasons
1. [Most common distraction reason 1]
2. [Most common distraction reason 2]
3. [Most common distraction reason 3]

## Intervention Effectiveness Evaluation
[Evaluation of intervention effectiveness based on data]

## Improvement Suggestions
1. [Specific suggestion 1: detailed explanation]
2. [Specific suggestion 2: detailed explanation]
3. [Specific suggestion 3: detailed explanation]
"""
    prompt_part3 = """
Notes:
- Date format must use ISO standard (YYYY-MM-DD)
- The values for focused and distracted should be integers
- common_reasons should extract the 3-5 main distraction reasons from historical data
- improvement_suggestions should give 3-5 concrete and actionable improvement suggestions
"""

    return prompt_part1 + prompt_part2 + prompt_part3

# Automated process (for demonstration, actual use should pass date range from main program)
if __name__ == '__main__':
    # Example only, in actual use should be passed from main program
    start_date = "2023-11-01"
    end_date = "2023-11-07"
    directory_path = "./FocusReports/daily_report"

    files = get_files_for_date_range(start_date, end_date, directory_path)
    if files:
        log_summary = parse_specific_files(files)
        summary_text = generate_summary_text(log_summary)
        final_prompt = generate_prompt(summary_text)
        # Output or pass final_prompt to LLM model for analysis
        print(final_prompt)
    else:
        print(f"No log files found in the date range {start_date} to {end_date}")
