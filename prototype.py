# This code uses TextBlob to classify text by sentiment and colorizes it accordingly.
# Make sure to install the TextBlob library before running this code.
# You can install it using: pip install textblob  

from textblob import TextBlob

def classify_text_by_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    if polarity < -0.5:
        return 'red'      # Highly sensitive or negative
    elif polarity < 0:
        return 'orange'   # Moderately sensitive
    elif polarity == 0:
        return 'yellow'   # Mildly sensitive
    elif polarity <= 0.5:
        return 'green'    # Safe and positive
    else:
        return 'blue'     # Very safe or objective

def wrap_in_color(text, color):
    return f'<span style="color:{color}">{text}</span>'

def analyze_and_colorize(text):
    sentences = text.split('.')
    result = ''
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            color = classify_text_by_sentiment(sentence)
            result += wrap_in_color(sentence + '.', color) + ' '
    return result.strip()

# Example
text = "I hate sharing my phone number. I enjoy working with data. My name is Roshini."
html_output = analyze_and_colorize(text)
print(html_output)

# Install textblob
# !pip install textblob