from src.triage import detect_red_flags, extract_symptoms

text = "5-year-old vomited twice but is able to drink small sips of water. No other symptoms."
flags = detect_red_flags(text)
symptoms = extract_symptoms(text)
print(f'Text: {text}')
print(f'Detected red flags: {flags}')
print(f'Detected symptoms: {symptoms}')
