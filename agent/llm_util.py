import os
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

def get_structured_llm(schema: type[BaseModel], model_name: str = "gemini-1.5-flash", temperature: float = 0.0):
    """
    Get a Gemini LLM configured to return structured output matching the provided Pydantic schema.
    """
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    return llm.with_structured_output(schema)
