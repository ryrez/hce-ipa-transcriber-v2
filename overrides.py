import json
from collections import defaultdict
import os

def update_override_dict(log_file="corrections_log.jsonl", output_file="override_dict.json"):
    """Update override dictionary from corrections log"""
    corrections = {}
    
    if not os.path.exists(log_file):
        # Create empty override dict if no log exists
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump({}, f, indent=2)
        return
    
    try:
        with open(log_file, "r", encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    
                    # Handle word-level corrections
                    if data.get("type") == "word":
                        word_clean = data.get("word_clean", data.get("text", "").lower())
                        
                        # Priority: manual correction > selected option
                        if data.get("manual_correction"):
                            corrections[word_clean] = data["manual_correction"]
                        elif data.get("final_choice"):
                            corrections[word_clean] = data["final_choice"]
                        elif data.get("selected"):
                            corrections[word_clean] = data["selected"]
                    
                    # Handle legacy sentence-level corrections
                    elif data.get("type") != "sentence" and not data.get("type"):
                        text = data.get("text", "").lower()
                        if data.get("correction"):
                            corrections[text] = data["correction"]
                        elif data.get("final_choice"):
                            corrections[text] = data["final_choice"]
                        elif data.get("selected"):
                            corrections[text] = data["selected"]
    except Exception as e:
        print(f"Error reading corrections log: {e}")
    
    # Save updated override dictionary
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(corrections, f, indent=2, ensure_ascii=False)
    
    print(f"Updated override dictionary with {len(corrections)} corrections")
    
    print(f"Updated override dictionary with {len(corrections)} corrections")