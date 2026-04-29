from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

text = """
Climate change is increasing global temperatures, causing extreme weather events,
rising sea levels, and affecting ecosystems worldwide.
"""

result = summarizer(text, max_length=40, min_length=15, do_sample=False)

print(result)
