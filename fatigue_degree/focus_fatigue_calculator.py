import re
import json
from datetime import datetime
from collections import Counter
import requests

def read_focus_log(file_path):
    logs = []
    pattern = re.compile(r'\[(.*?)\] Output: ({.*?})')
    with open(file_path, "r", encoding='utf-8') as f:
        for line in f:
            match = pattern.match(line.strip())
            if not match:
                continue
            ts_str, json_str = match.groups()
            try:
                log_dict = json.loads(json_str)
                log_dict['timestamp'] = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                logs.append(log_dict)
            except Exception as e:
                pass
    return logs

def filter_today_logs(logs, ref_date=None):
    if not ref_date:
        ref_date = datetime.now()
    today = ref_date.date()
    today_logs = [log for log in logs if log['timestamp'].date() == today]
    return today_logs

def compute_fatigue_score(logs):
    if not logs:
        return 0, 0, 0
    total = len(logs)
    distraction = sum(1 for log in logs if log['status'].startswith("2"))
    fatigue_score = distraction / total * 100
    return fatigue_score, distraction, total

def extract_main_distraction_reasons(logs, topn=2):
    reasons = []
    for log in logs:
        if log.get("status", "").startswith("2"):
            reason = log.get("reason", "")
            # Keep only the key information, remove application names, etc.
            reason = re.sub(r'\(.*?\)', '', reason)
            reasons.append(reason)
    counter = Counter(reasons)
    return [item for item, _ in counter.most_common(topn)]

def get_fatigue_level_and_advice(score):
    if score < 20:
        level = "Good Focus State"
        advice = "State is excellent, you can complete tasks efficiently. Keep up the good focus!"
        color = "Blue"
        intervene = False
    elif score < 40:
        level = "Mild Fatigue"
        advice = "Attention has slightly declined. It is recommended to take a short break, hydrate, or do light stretching."
        color = "Sky Blue ~ Orange"
        intervene = True
    elif score < 60:
        level = "Moderate Fatigue"
        advice = "Distraction frequency is high. Please take a 5-15 minute break to avoid continuous fatigue."
        color = "Orange"
        intervene = True
    else:
        level = "High Fatigue"
        advice = "Cognitive resources have significantly decreased. It is recommended to stop working and rest away from the screen."
        color = "Red"
        intervene = True
    return level, advice, color, intervene

def generate_intervention_report(level, fatigue_score, distraction_reasons):
    reasons_str = "; ".join(distraction_reasons) if distraction_reasons else "No main distraction reasons available"
    system_prompt = (
        "You are an intelligent health assistant, proficient in active-passive control theory analysis. Please generate a structured and personalized fatigue relief strategy report based on fatigue detection data.\n"
        "The report should include:\n"
        "1. Brief description of fatigue state (distraction rate and level).\n"
        "2. Brief list of main distraction triggers.\n"
        "3. Specific proactive intervention suggestions (such as short breaks, playing soothing music, task switching, work style adjustment, etc. Each suggestion should be concise, specific, and actionable).\n"
        "4. A one-sentence popular science explanation of active-passive control theory.\n"
        "The writing should be organized, friendly, yet authoritative.\n"
    )

    user_prompt = (
        f"Current fatigue level: {level}\n"
        f"Distraction rate score: {fatigue_score:.2f}\n"
        f"Main distraction triggers: {reasons_str}\n"
    )

    data = {
        "model": "Qwen2.5:7b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    try:
        response = requests.post(
            "http://120.26.224.38:11434/api/chat",
            json=data,
            stream=True,       # <- use stream=True!
            timeout=30
        )
        response.raise_for_status()
        contents = []
        for line in response.iter_lines():
            if not line:
                continue
            try:
                obj = json.loads(line.decode('utf-8'))
                # Ollama new version output: data/message part
                # Compatible with different formats
                if "message" in obj and "content" in obj["message"]:
                    contents.append(obj["message"]["content"])
                elif "content" in obj:
                    contents.append(obj["content"])
            except Exception as e:
                continue
        final_text = "".join(contents).strip()
        if final_text:
            return final_text
        else:
            return "Intelligent report generation failed: No valid response received."
    except Exception as e:
        return f"Intelligent report generation failed: {str(e)}"

def focus_fatigue_calculator():
    file_path = "../focus_log.txt"  # Or adjust via parameter
    # 1. Read logs
    logs = read_focus_log(file_path)

    today_logs = filter_today_logs(logs)
    fatigue_score, n_distraction, n_total = compute_fatigue_score(today_logs)
    level, advice, color, intervene = get_fatigue_level_and_advice(fatigue_score)
    distraction_reasons = extract_main_distraction_reasons(today_logs, topn=2)

    # 3. Print brief information
    print(f"[Statistics Date] {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Total records: {n_total}, Distraction records: {n_distraction}")
    print(f"Today's fatigue score: {fatigue_score:.2f} (Distraction rate)")
    print(f"Fatigue level: {level} ({color})")
    print(f"General advice: {advice}")
    print("-" * 50)
    # 4. If intervention is needed, generate a detailed report
    if intervene:
        print("Generating intervention report, please wait...")
        report = generate_intervention_report(level, fatigue_score, distraction_reasons)
        print(report)
