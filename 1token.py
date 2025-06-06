import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print(f"⚠️ Модель '{model}' не найдена. Используется базовая кодировка.")
        encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    return len(tokens)

def main():
    import sys

    model = "gpt-4"  # Можно заменить на gpt-3.5-turbo, gpt-4o и т.д.

    if len(sys.argv) > 1:
        # Чтение из файла, если указан путь
        file_path = sys.argv[1]
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        print("🔹 Вставь текст (нажми Ctrl+D или Ctrl+Z, чтобы закончить):")
        text = sys.stdin.read()

    token_count = count_tokens(text, model)
    print(f"\n📊 Количество токенов для модели '{model}': {token_count}")

if __name__ == "__main__":
    main()
