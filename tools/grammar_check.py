from utils.groq_integration import GroqClient

def grammar_check(groq_client, assignment_text):
    prompt = f"""
Evaluate the following assignment for grammar and language quality. For each category below, provide specific feedback and suggestions. Highlight areas where grammar could be improved, where the language could be clearer, and identify any errors.

Instructions:

1. **Spelling**: Identify any spelling mistakes or incorrect word usage.
2. **Punctuation**: Check for missing or incorrect punctuation marks that may impact readability.
3. **Sentence Structure**: Evaluate the structure of sentences, highlighting any overly complex, fragmented, or run-on sentences.
4. **Language Clarity**: Suggest rephrasing for sentences that are unclear, verbose, or could benefit from simpler language.

- Provide your report in Markdown format.
- Use clear headings and bullet points under each category.

Assignment:
{assignment_text}

Provide a detailed grammar and language quality report.
"""
    messages = [{"role": "user", "content": prompt}]
    response = groq_client.get_groq_response(messages)
    return response
