from cleaner import strip_headers_footers

pages = [
    "HEADER\nIntro line 1\nImportant content page 1\nMore content page 1\nFOOTER",
    "HEADER\nIntro line 2\nImportant content page 2\nMore content page 2\nFOOTER",
    "HEADER\nIntro line 3\nImportant content page 3\nMore content page 3\nFOOTER",
]

result = strip_headers_footers(pages, window=1)

for i, page in enumerate(result):
    print(f"\n--- Page {i+1} ---")
    print(page)
