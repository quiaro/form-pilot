def clean_llm_response(text):
    """
    Remove <think> and </think> tags from text and strip whitespace/newlines.
    This is specific to the Qwen3 model:
    https://qwenlm.github.io/blog/qwen3/#advanced-usages
    Even when using "/no_think" in the prompt, the model still returns the think tags.
    
    Args:
        text (str): Input string containing think tags
        
    Returns:
        str: Cleaned string with think tags removed and whitespace stripped
    """
    # Find the positions of the tags
    start = text.find('<think>')
    end = text.find('</think>')
    
    if start != -1 and end != -1:
        # Remove everything from <think> to </think> including the tags
        cleaned = text[:start] + text[end + 8:]  # 8 = len('</think>')
    else:
        cleaned = text
    
    # Strip leading/trailing whitespace and newlines
    return cleaned.strip()
