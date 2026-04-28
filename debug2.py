from src.triage import detect_red_flags, extract_symptoms

text = "Baby has minor cuts from playing. No bleeding, alert and playing normally."
flags = detect_red_flags(text)
symptoms = extract_symptoms(text)
print(f'Text: {text}')
print(f'Detected red flags: {flags}')
print(f'Detected symptoms: {symptoms}')
