"""Tudo o que é criptografia de passwords vive aqui (e só aqui)."""

from pwdlib import PasswordHash

# Argon2: algoritmo vencedor da Password Hashing Competition.
# "recommended()" escolhe parâmetros seguros por nós (memória, iterações, salt aleatório).
_hasher = PasswordHash.recommended()


def gerar_hash(password: str) -> str:
    """Transforma a password num hash irreversível (com salt) para guardar na BD."""
    return _hasher.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    """Volta a calcular o hash da password escrita e compara com o guardado."""
    return _hasher.verify(password, password_hash)
