#!/usr/bin/env python3
"""Debug EN_MONITOR_03 case."""

from src.triage import extract_symptoms, detect_red_flags, classify_severity, extract_age
from src.retrieval import get_retriever

text = "5-year-old vomited twice but is able to drink small sips of water. No other symptoms."

print(f"Text: {text}")
print(f"Red flags: {detect_red_flags(text)}")
print(f"Symptoms: {extract_symptoms(text)}")
print(f"Age: {extract_age(text)}")

retriever = get_retriever()

# Simulate full triage
red_flags = detect_red_flags(text)
symptoms = extract_symptoms(text)
age_months = extract_age(text)

severity, confidence, reasoning, is_weak = classify_severity(
    red_flags=red_flags,
    symptoms=symptoms,
    age_months=age_months,
    temperature=None,
    temperature_unit=None,
    retriever=retriever,
)

print(f"\nClassification:")
print(f"Severity: {severity}")
print(f"Confidence: {confidence}")
print(f"Is weak: {is_weak}")
print(f"Reasoning: {reasoning}")
