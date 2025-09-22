import streamlit as st
import spacy
from textblob import TextBlob
import pandas as pd
import re

# Load NLP model
nlp = spacy.load("en_core_web_sm")

PII_ENTITIES = {"PERSON", "GPE", "ORG", "EMAIL", "LOC", "DATE", "TIME", "PHONE", "MONEY"}

# Function: Redact text
def redact_text(text):
    doc = nlp(text)
    redacted_text = text
    redacted_items = []

    for ent in reversed(doc.ents):
        if ent.label_ in PII_ENTITIES:
            redacted_items.append((ent.text, ent.label_))
            redacted_text = (
                redacted_text[:ent.start_char] +
                f"[{ent.label_}_REDACTED]" +
                redacted_text[ent.end_char:]
            )
    return redacted_text, redacted_items, doc

# Function: Highlight spans
def highlight_pii(doc):
    output = ""
    last_idx = 0
    for ent in doc.ents:
        output += doc.text[last_idx:ent.start_char]
        if ent.label_ in PII_ENTITIES:
            output += f"<span style='background-color:#ffcccc;'>{ent.text}</span>"
        else:
            output += ent.text
        last_idx = ent.end_char
    output += doc.text[last_idx:]
    return output

# Function: Sentiment detection
def get_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.5:
        return "😊 Positive"
    elif polarity < -0.5:
        return "😠 Negative"
    

# Function: Export redacted items
def export_log_csv(redacted_items):
    df = pd.DataFrame(redacted_items, columns=["Entity", "Label"])
    return df.to_csv(index=False).encode('utf-8')

# Function: Auto-correct & format ticket note
def autocorrect_ticket_note(text):
    text = text.strip().capitalize()
    text = re.sub(r"\byou\b", "the caller", text, flags=re.IGNORECASE)
    text = re.sub(r"\bI\b", "we", text)
    text = re.sub(r"\bI'm\b", "we're", text, flags=re.IGNORECASE)
    text = re.sub(r"\bI've\b", "we've", text, flags=re.IGNORECASE)

    blob = TextBlob(text)
    corrected_text = str(blob.correct())
    corrected_text = corrected_text[0].upper() + corrected_text[1:]
    issue_summary = generate_issue_summary(corrected_text)
    return f"{corrected_text} Issue Type: {issue_summary}"

# Function: Auto-generate issue type
def generate_issue_summary(text):
    text = text.lower()
    if "login" in text:
        return "Login issue reported by the caller."
    elif "reset" in text:
        return "Reset request raised by the caller."
    elif "access" in text:
        return "Access issue encountered by the caller."
    elif "error" in text:
        return "Application error experienced by the caller."
    else:
        return "Support request raised by the caller."

# --- Streamlit UI ---
st.set_page_config(page_title="LLM Privacy Gate", layout="centered")
st.title("🔐 LLM Privacy Gate")
st.write("Detects, redacts, and formats sensitive information before LLM interaction.")

user_input = st.text_area("✍️ Enter text to process:", height=200)
mode = st.radio("🚦 Action on sensitive data:", ["Replace", "Warn", "Block"])

if st.button("🔍 Analyze & Redact"):
    if not user_input.strip():
        st.warning("Please enter some text.")
    else:
        redacted_text, redacted_items, doc = redact_text(user_input)
        sentiment = get_sentiment(user_input)

        st.subheader("📄 Original Input")
        st.write(user_input)

        st.subheader("🖍️ Highlighted Entities")
        st.markdown(highlight_pii(doc), unsafe_allow_html=True)

        st.subheader("🧼 Redacted Output")
        if redacted_items:
            if mode == "Block":
                st.error("❌ Input blocked due to sensitive data.")
                st.stop()
            elif mode == "Warn":
                st.warning("⚠️ Sensitive data found. Proceed with caution.")
        else:
            st.success("✅ No PII detected.")

        st.code(redacted_text, language="text")

        st.subheader("🧠 Sentiment")
        st.info(f"Sentiment: {sentiment}")

        if redacted_items:
            csv = export_log_csv(redacted_items)
            st.download_button("⬇️ Download Redaction Log (CSV)", csv, "redaction_log.csv", "text/csv")

        # Auto-correction output
        st.subheader("🛠️ Auto-corrected Ticket Note")
        formatted_note = autocorrect_ticket_note(user_input)
        st.success(formatted_note)

from fpdf import FPDF

def generate_ticket_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    return pdf.output(dest="S").encode("latin-1")  # Return as bytes

def generate_log_pdf(items):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Redaction Log", ln=True, align="C")
    for entity, label in items:
        pdf.cell(200, 10, f"{entity} - {label}", ln=True)
    return pdf.output(dest="S").encode("latin-1")

import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def call_llm(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or gpt-4 if you prefer
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM Error: {str(e)}"

def call_llm(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or gpt-4 if you prefer
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM Error: {str(e)}"
 
