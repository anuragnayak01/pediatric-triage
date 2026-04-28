#!/usr/bin/env python3
"""Debug EN_MONITOR_03 case."""

from src.triage import extract_symptoms, detect_red_flags, extract_temperature, extract_age, extract_language

text = "My child is vomiting but can drink and eat small amounts."

print(f"Text: {text}")
print(f"Language: {extract_language(text)}")
print(f"Red flags: {detect_red_flags(text)}")
print(f"Symptoms: {extract_symptoms(text)}")
print(f"Temperature: {extract_temperature(text)}")
print(f"Age: {extract_age(text)}")
