from pathlib import Path
import secrets

ENV_FILE = Path(".env")
KEY_NAME = "FLASK_SECRET_KEY"

def generate_secret_key(length=48):
    return secrets.token_urlsafe(length)

def update_env_file():
    secret_key = generate_secret_key()

    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    updated = False
    new_lines = []

    for line in lines:
        if line.startswith(f"{KEY_NAME}="):
            new_lines.append(f"{KEY_NAME}={secret_key}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{KEY_NAME}={secret_key}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    print(f"Chave gerada com sucesso:\n{secret_key}")
    print(f"\nArquivo atualizado: {ENV_FILE.resolve()}")

if __name__ == "__main__":
    update_env_file()