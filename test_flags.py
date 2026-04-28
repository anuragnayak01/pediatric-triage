from src.triage import detect_red_flags

tests = [
    'Baby lips are turning blue and he is not breathing well.',
    'My 3-year-old is struggling to breathe, wheezing, having retractions.',
    'My child had a seizure lasting 2 minutes.',
    'I have a cold with runny nose and cough.',
]
for text in tests:
    flags = detect_red_flags(text)
    print(f'Flags for "{text[:40]}...": {flags}')
