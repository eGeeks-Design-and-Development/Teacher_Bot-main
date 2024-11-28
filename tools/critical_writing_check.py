from utils.groq_integration import GroqClient

def critical_writing_check(groq_client, assignment_text):
    prompt = f"""
Evaluate the following assignment for critical analysis and writing quality. For each category below, provide specific feedback and suggestions. Highlight areas where the argument could be strengthened, where more critical thinking is needed, or where the writing could be clearer and more concise. 

Instructions:

1. **Argument Structure**: Analyze the coherence and logical flow of arguments. Identify gaps or areas needing improvement.
2. **Critical Analysis**: Evaluate the depth of analysis. Highlight any areas where more critical thinking or insight is required.
3. **Evidence and Support**: Assess the quality and relevance of evidence used to support arguments. Note where stronger or additional evidence could improve the argument.
4. **Clarity and Conciseness**: Check for readability, clear expression, and conciseness. Suggest rephrasing for overly complex or verbose sentences.
5. **Grammar and Syntax**: Identify grammatical errors or awkward syntax that may impede readability.

Instructions:

- Provide the report in Markdown format.
- Use clear headings and bullet points under each category.
- Include an overall score out of 10 at the end, with individual scores for each category out of 2.

Assignment:
{assignment_text}

Provide a detailed critical writing report.
"""
    messages = [{"role": "user", "content": prompt}]
    response = groq_client.get_groq_response(messages)
    return response
