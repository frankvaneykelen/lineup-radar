"""
Azure OpenAI client setup and utilities.
"""

import os
import sys
import json
from typing import Optional
import requests


def get_azure_openai_credentials() -> tuple[str, str, str]:
    """
    Get Azure OpenAI credentials from environment variables.
    
    Returns:
        Tuple of (api_key, endpoint, deployment)
        
    Raises:
        SystemExit: If required credentials are not set
    """
    azure_key = os.getenv("AZURE_OPENAI_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    
    if not azure_key or not azure_endpoint:
        print(f"\n✗ ERROR: Azure OpenAI credentials not set!")
        print(f"  Please set AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT environment variables")
        print(f"\n  Example (PowerShell):")
        print(f"    $env:AZURE_OPENAI_KEY = 'your-key'")
        print(f"    $env:AZURE_OPENAI_ENDPOINT = 'https://your-resource.cognitiveservices.azure.com'")
        print(f"    $env:AZURE_OPENAI_DEPLOYMENT = 'gpt-4o'")
        sys.exit(1)
    
    return azure_key, azure_endpoint, azure_deployment


def get_azure_openai_client():
    """
    Get configured Azure OpenAI client.
    
    Returns:
        Tuple of (api_key, endpoint, deployment) for making requests
    """
    return get_azure_openai_credentials()


def call_azure_openai(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: Optional[int] = None
) -> str:
    """
    Call Azure OpenAI Chat Completion API.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        temperature: Sampling temperature (0.0 to 2.0)
        max_tokens: Maximum tokens in response (optional)
        
    Returns:
        Response text from the model
        
    Raises:
        requests.RequestException: If API call fails
    """
    api_key, endpoint, deployment = get_azure_openai_credentials()
    
    url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version=2024-12-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    payload = {
        "messages": messages,
        "temperature": temperature
    }
    
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    return result['choices'][0]['message']['content']


def translate_text(
    text: str,
    from_lang: str = "Dutch",
    to_lang: str = "English"
) -> str:
    """
    Translate text using Azure OpenAI.
    
    Args:
        text: Text to translate
        from_lang: Source language (default: Dutch)
        to_lang: Target language (default: English)
        
    Returns:
        Translated text
    """
    if not text or not text.strip():
        return ""
    
    messages = [
        {
            "role": "system",
            "content": f"You are a professional translator. Translate the following text from {from_lang} to {to_lang}. Preserve the tone and style. Return ONLY the translated text, nothing else."
        },
        {
            "role": "user",
            "content": text
        }
    ]
    
    try:
        return call_azure_openai(messages, temperature=0.3)
    except Exception as e:
        print(f"⚠️  Translation failed: {e}")
        return text  # Return original text if translation fails


def enrich_with_ai(prompt: str, temperature: float = 0.7) -> str:
    """
    Get AI-generated content using Azure OpenAI.
    
    Args:
        prompt: Prompt for the model
        temperature: Sampling temperature (default: 0.7)
        
    Returns:
        Generated text
    """
    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    return call_azure_openai(messages, temperature=temperature)


def clean_scraped_text(text: str) -> str:
    """
    Clean up text scraped from HTML to fix whitespace and formatting issues.
    
    This fixes common HTML parsing artifacts like:
    - Missing spaces between words (e.g., "presentAvishag" -> "present Avishag")
    - Missing spaces before/after parentheses (e.g., "bandCumgirl8(4AD)" -> "band Cumgirl8 (4AD)")
    - Doubled spaces, missing punctuation spacing, etc.
    
    Args:
        text: Raw scraped text
        
    Returns:
        Cleaned text with proper spacing and formatting
    """
    if not text or not text.strip():
        return ""
    
    # Quick check: if text looks clean (no obvious issues), skip GPT call
    # Check for missing spaces: lowercase letter followed by uppercase letter without space
    import re
    has_spacing_issues = bool(re.search(r'[a-z][A-Z]', text))
    has_paren_issues = bool(re.search(r'[a-zA-Z]\(', text))  # Letter directly before (
    has_comma_issues = bool(re.search(r',[A-Z]', text))  # Comma followed directly by capital
    
    if not has_spacing_issues and not has_paren_issues and not has_comma_issues:
        return text  # Text looks clean, no need to process
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are a text cleanup assistant. Fix whitespace and formatting issues in scraped HTML text. "
                "Add missing spaces between words, add spaces before opening parentheses and after closing parentheses when needed, "
                "add spaces after commas and periods when missing, fix punctuation spacing. "
                "Preserve the EXACT original wording, meaning, capitalization, and names. "
                "Return ONLY the cleaned text with no explanations or comments."
            )
        },
        {
            "role": "user",
            "content": text
        }
    ]
    
    try:
        cleaned = call_azure_openai(messages, temperature=0.1)  # Low temperature for consistency
        # Remove any quotes that GPT might add around the response
        cleaned = cleaned.strip('"').strip("'").strip()
        return cleaned
    except Exception as e:
        print(f"  ⚠️  Text cleanup failed: {e}")
        return text  # Return original text if cleanup fails
