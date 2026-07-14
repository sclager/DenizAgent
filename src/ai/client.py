import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key or api_key == "buraya_api_anahtarin_gelecek":
        raise ValueError(
            "OPENAI_API_KEY tanımlı değil. "
            ".env dosyasına geçerli bir API anahtarı ekleyin."
        )

    return OpenAI(api_key=api_key)


def get_model_name() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-5.6")