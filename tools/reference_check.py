from utils.groq_integration import GroqClient

def reference_check(groq_client, assignment_text, module_text, reference_style):
    prompt = f"""
Analyze the references in the following assignment based on the required referencing style ({reference_style}). Check for the following:

1. **Completeness of Required References**: Ensure all necessary citations from the module materials are included. List any missing references that are essential for supporting the arguments.
2. **Formatting Accuracy**: Verify that all references adhere to the specified style ({reference_style}), checking for consistent formatting in author names, publication dates, titles, and source information.
3. **In-Text Citations**: Check that all in-text citations match the reference list and are correctly formatted.
4. **Consistency of Style**: Ensure consistency in referencing throughout the document, noting any variations in style or incomplete references.

Instructions:

- Provide your report in Markdown format.
- Use clear headings and bullet points under each category.
- If any specific corrections are required, include examples.

Module Materials:
{module_text}

Assignment:
{assignment_text}

Provide a detailed and structured reference check report.
"""
    response = groq_client.get_groq_response([{"role": "user", "content": prompt}])
    return response
