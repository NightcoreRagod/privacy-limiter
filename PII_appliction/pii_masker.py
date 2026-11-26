from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

text = """
Contact Priya Sharma at priya.sharma@example.com or +91 98765 43210.
Her card number is 4111 1111 1111 1111.
She lives in Bengaluru, India.
"""

# 1. Detect PII
analyzer = AnalyzerEngine()
results = analyzer.analyze(
    text=text,
    language="en",
    entities=[
        "PERSON",
        "EMAIL_ADDRESS",
        "PHONE_NUMBER",
        "CREDIT_CARD",
        "LOCATION",
    ],
)

# 2. Apply a policy per entity type
anonymizer = AnonymizerEngine()

anonymized = anonymizer.anonymize(
    text=text,
    analyzer_results=results,
    operators={
        "PERSON": OperatorConfig("replace", {"new_value": "[PERSON]"}),
        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
        "PHONE_NUMBER": OperatorConfig(
            "mask",
            {
                "masking_char": "*",
                "chars_to_mask": 8,
                "from_end": True,
            },
        ),
        "CREDIT_CARD": OperatorConfig("redact", {}),
        "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
        "DEFAULT": OperatorConfig("redact", {}),
    },
)

print(anonymized.text)