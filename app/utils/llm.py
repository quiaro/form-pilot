import os
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

def get_llm(type: str, temperature: float = 0.0):
    """
    Get an LLM instance based on the specified type.
    
    Args:
        type (str): The type of LLM to use (PREFILL_LLM, QUESTIONS_LLM, ANSWER_JUDGE_LLM, etc.)
        temperature (float, optional): The temperature for the model. Defaults to 0.0.
        
    Returns:
        An instance of either ChatOpenAI or ChatOllama
    """
    model_name = os.getenv(type)
    # TODO: use a more robust way to check if the model is an OpenAI model
    is_openai_model = model_name.startswith("gpt")
    if model_name is None:
        raise ValueError(f"Model name not found for {type}")

    if is_openai_model:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        return ChatOpenAI(model=model_name, temperature=temperature)
    else:
        return ChatOllama(model=model_name, temperature=temperature)

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
