class PIIData {
  index int
  dataType string
  value string
}

class PIIExtraction {
  privateData PIIData[]
  containsSensitivePII bool @description("E.g. SSN")
}

function ExtractPII(document: string) -> PIIExtraction {
  client "openai/gpt-5-mini"
  prompt #"
    Extract all personally identifiable information (PII) from the given document. Look for items like:
    - Names
    - Email addresses
    - Phone numbers
    - Addresses
    - Social security numbers
    - Dates of birth
    - Any other personal data

    {{ ctx.output_format }}

    {{ _.role("user") }} 
    
    {{ document }}
  "#
}
