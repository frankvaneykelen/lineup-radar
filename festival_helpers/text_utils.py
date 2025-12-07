"""Text formatting utilities for festival content."""

import re


def markdown_to_html(text: str) -> str:
    """
    Convert basic markdown formatting to HTML.
    
    Supports:
    - **bold** -> <strong>
    - *italic* -> <em>
    - Paragraph breaks (double newlines)
    
    Args:
        text: Markdown-formatted text
        
    Returns:
        HTML-formatted text with paragraphs
    """
    if not text:
        return ""
    
    # Convert **bold** to <strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert *italic* to <em> (but not already processed bold markers)
    text = re.sub(r'(?<!</strong>)\*(.+?)\*(?!<strong>)', r'<em>\1</em>', text)
    
    # Split into paragraphs (double newlines or more)
    paragraphs = re.split(r'\n\s*\n+', text.strip())
    
    # Wrap each paragraph in <p> tags
    html_paragraphs = [f'<p>{p.strip()}</p>' for p in paragraphs if p.strip()]
    
    return '\n'.join(html_paragraphs)
