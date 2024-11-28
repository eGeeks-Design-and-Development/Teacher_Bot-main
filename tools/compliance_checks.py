from utils.groq_integration import GroqClient
from typing import Dict, List

def check_assessment_compliance(groq_client, assignment_text, assessment_text):
    """
    Highly focused assessment compliance checker with precise evaluation criteria
    """
    prompt = f"""
As an academic evaluator, provide a precise, focused analysis comparing the assignment against the assessment brief.
- Do not mentiond word count (skip it)
- Do not mention submission Date and time

Assessment Brief: {assessment_text}
Assignment: {assignment_text}

Analyze using this exact format:

# Assessment Compliance Analysis

## ✓ Met Requirements
- [One-line bullet: Specific achievement + Brief example]
- [One-line bullet: Specific achievement + Brief example]
- [One-line bullet: Specific achievement + Brief example]

## ✗ Missing Requirements
- [One-line bullet: Specific gap + Required element]
- [One-line bullet: Specific gap + Required element]
- [One-line bullet: Specific gap + Required element]

## ⚡ Priority Actions
1. [Most critical action needed - one line]
2. [Second priority action - one line]
3. [Third priority action - one line]

## 📊 Score: X/10
[One sentence overall assessment]

Rules:
- Do not mentiond word count (skip it)
- Do not mention submission Date and time
- Maximum 3 points per section
- Each bullet must be specific and one line only
- Use concrete examples, not general statements
- Focus only on major elements
"""
    messages = [{"role": "user", "content": prompt}]
    response = groq_client.get_groq_response(messages)
    return response

def check_module_compliance(groq_client, assignment_text, module_text):
    """
    Highly focused module compliance checker with precise alignment criteria
    """
    prompt = f"""
As an academic evaluator, provide a precise, focused analysis of module content alignment.

Module Materials: {module_text}
Assignment: {assignment_text}

Analyze using this exact format:

# Module Content Alignment

## ✓ Strong Alignment
- [One-line bullet: Module concept + How well applied]
- [One-line bullet: Module concept + How well applied]
- [One-line bullet: Module concept + How well applied]

## ✗ Missing Content
- [One-line bullet: Missing concept + Why needed]
- [One-line bullet: Missing concept + Why needed]
- [One-line bullet: Missing concept + Why needed]

## ⚡ Key Improvements
1. [Most critical improvement - one line]
2. [Second priority improvement - one line]
3. [Third priority improvement - one line]

## 📊 Score: X/10
[One sentence overall alignment assessment]

Rules:
- Maximum 3 points per section
- Each bullet must reference specific module concepts
- One line per point only
- Focus on major elements only
"""
    messages = [{"role": "user", "content": prompt}]
    response = groq_client.get_groq_response(messages)
    return response
