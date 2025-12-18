#!/usr/bin/env python3
"""
Extract text from an image using Azure OpenAI Vision.

This helper uses the Azure OpenAI GPT-4o Vision API to perform OCR (Optical Character Recognition)
on image files. It's useful for extracting text from screenshots, photos, or scanned documents.

Example usage:
    python scripts/helpers/extract_image_text.py path/to/image.jpg
    
Or import and use in your own scripts:
    from helpers.extract_image_text import extract_text_from_image
    text = extract_text_from_image("image.jpg")
"""

import sys
import os
import base64
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from helpers.ai_client import get_azure_openai_credentials
import requests


def extract_text_from_image(image_path: str, prompt: str = None) -> str:
    """
    Extract text from an image using Azure OpenAI Vision API.
    
    Args:
        image_path: Path to the image file (jpg, png, etc.)
        prompt: Optional custom prompt for text extraction. Defaults to basic OCR.
        
    Returns:
        Extracted text as a string
        
    Raises:
        FileNotFoundError: If image file doesn't exist
        requests.RequestException: If API call fails
    """
    
    # Check if image exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Get credentials
    api_key, endpoint, deployment = get_azure_openai_credentials()
    
    # Read and encode image
    with open(image_path, 'rb') as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Determine file extension for MIME type
    ext = Path(image_path).suffix.lower()
    mime_type = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }.get(ext, 'image/jpeg')
    
    # Default prompt if none provided
    if prompt is None:
        prompt = "Please extract all text from this image. Return only the extracted text, preserving the layout and formatting as much as possible."
    
    # Prepare API request
    url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/chat/completions?api-version=2024-12-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4000,
        "temperature": 0.1
    }
    
    # Make request
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    
    result = response.json()
    return result['choices'][0]['message']['content']


def main():
    """Command-line interface for extracting text from images."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/helpers/extract_image_text.py <image_path> [custom_prompt]")
        print("\nExample:")
        print('  python scripts/helpers/extract_image_text.py photo.jpg')
        print('  python scripts/helpers/extract_image_text.py lineup.png "Extract artist names from this lineup poster"')
        sys.exit(1)
    
    image_path = sys.argv[1]
    custom_prompt = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Extracting text from: {image_path}")
    print("=" * 80)
    
    try:
        text = extract_text_from_image(image_path, custom_prompt)
        print("\n--- EXTRACTED TEXT ---\n")
        print(text)
        print("\n" + "=" * 80)
        print(f"\nTotal characters extracted: {len(text)}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
