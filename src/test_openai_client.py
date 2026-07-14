from src.ai.client import get_model_name, get_openai_client


def main() -> None:
    client = get_openai_client()
    model = get_model_name()

    response = client.responses.create(
        model=model,
        input="Sadece TAMAM yaz.",
    )

    print("Model:", model)
    print("Yanıt:", response.output_text)


if __name__ == "__main__":
    main()