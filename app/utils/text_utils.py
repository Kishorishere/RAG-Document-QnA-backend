import re
from typing import List


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing line breaks.
    
    Args:
        text: Input text
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    text = remove_control_characters(text)
    text = normalize_whitespace(text)
    text = text.strip()
    
    return text


def normalize_whitespace(text: str) -> str:
    """
    Convert multiple spaces to single space.
    
    Args:
        text: Input text
    
    Returns:
        Normalized text
    """
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text


def remove_special_characters(text: str, keep: str = "") -> str:
    """
    Remove special characters except those specified.
    
    Args:
        text: Input text
        keep: Characters to keep (e.g., ".,!?")
    
    Returns:
        Text with special characters removed
    """
    pattern = f"[^a-zA-Z0-9\\s{re.escape(keep)}]"
    return re.sub(pattern, '', text)


def remove_control_characters(text: str) -> str:
    """
    Remove control characters from text.
    
    Args:
        text: Input text
    
    Returns:
        Text without control characters
    """
    return re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def count_tokens_approximate(text: str) -> int:
    """
    Rough estimate of token count.
    
    Args:
        text: Input text
    
    Returns:
        Approximate token count
    """
    words = text.split()
    return int(len(words) * 1.3)


def extract_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Input text
    
    Returns:
        List of sentences
    """
    sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
    sentences = re.split(sentence_pattern, text)
    return [s.strip() for s in sentences if s.strip()]


def is_empty_or_whitespace(text: str) -> bool:
    """
    Check if text is empty or contains only whitespace.
    
    Args:
        text: Input text
    
    Returns:
        True if empty or whitespace only
    """
    return not text or text.isspace()


def remove_urls(text: str) -> str:
    """
    Remove URLs from text.
    
    Args:
        text: Input text
    
    Returns:
        Text without URLs
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.sub(url_pattern, '', text)


def remove_emails(text: str) -> str:
    """
    Remove email addresses from text.
    
    Args:
        text: Input text
    
    Returns:
        Text without emails
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.sub(email_pattern, '', text)


def extract_numbers(text: str) -> List[str]:
    """
    Extract all numbers from text.
    
    Args:
        text: Input text
    
    Returns:
        List of numbers as strings
    """
    return re.findall(r'\d+\.?\d*', text)


def count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Input text
    
    Returns:
        Word count
    """
    return len(text.split())