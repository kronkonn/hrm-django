"""
AES-256-CBC шифрование персональных данных согласно ФЗ-152.
Зависимость: pycryptodome (pip install pycryptodome)

Схема хранения: "enc:" + base64(IV[16] || ciphertext)
- IV генерируется случайно при каждом шифровании
- Ключ 256 бит (32 байта) из переменной окружения AES_SECRET_KEY
"""
import base64

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from django.db import models

_BLOCK_SIZE = 16          # AES block size, bytes
_ENCRYPTED_PREFIX = 'enc:'


def _get_key() -> bytes:
    """32-байтовый ключ AES-256 из settings.AES_SECRET_KEY."""
    from django.conf import settings
    raw = getattr(settings, 'AES_SECRET_KEY', 'hrm-default-key-32-bytes-long!!!')
    if isinstance(raw, str):
        raw = raw.encode('utf-8')
    # Обрезаем или дополняем нулями до 32 байт
    return (raw + b'\x00' * 32)[:32]


class AESEncryption:
    """
    AES-256-CBC шифрование строк.
    Зашифрованное значение: base64(IV[16 байт] || ciphertext).
    """

    def encrypt(self, value: str) -> str:
        """Шифрует строку. Возвращает base64-строку."""
        if not value:
            return value
        iv = get_random_bytes(_BLOCK_SIZE)
        cipher = AES.new(_get_key(), AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(pad(value.encode('utf-8'), _BLOCK_SIZE))
        return base64.b64encode(iv + ciphertext).decode('utf-8')

    def decrypt(self, value: str) -> str:
        """Расшифровывает base64-строку. При ошибке возвращает value как есть."""
        if not value:
            return value
        try:
            raw = base64.b64decode(value.encode('utf-8'))
            iv, ciphertext = raw[:_BLOCK_SIZE], raw[_BLOCK_SIZE:]
            cipher = AES.new(_get_key(), AES.MODE_CBC, iv)
            return unpad(cipher.decrypt(ciphertext), _BLOCK_SIZE).decode('utf-8')
        except Exception:
            return value  # plaintext-значение (до миграции) — вернуть как есть


_cipher = AESEncryption()


# ── Миксин ───────────────────────────────────────────────────────────────────

class EncryptedMixin:
    """
    Миксин для Django-полей: прозрачно шифрует при записи и расшифровывает
    при чтении из БД. Хранит данные в TEXT-колонке (get_internal_type='TextField').
    """

    def get_internal_type(self):
        return 'TextField'

    def get_prep_value(self, value):
        """Шифрует значение перед записью в БД."""
        if value is None or value == '':
            return value
        raw = str(value)
        if raw.startswith(_ENCRYPTED_PREFIX):
            return raw  # уже зашифровано
        return _ENCRYPTED_PREFIX + _cipher.encrypt(raw)

    def from_db_value(self, value, expression, connection):
        """Расшифровывает значение при чтении из БД."""
        return self._unwrap(value)

    def to_python(self, value):
        """Расшифровывает при десериализации и валидации."""
        return self._unwrap(value)

    def _unwrap(self, value):
        if value is None or value == '':
            return value
        if isinstance(value, str) and value.startswith(_ENCRYPTED_PREFIX):
            return _cipher.decrypt(value[len(_ENCRYPTED_PREFIX):])
        return value


# ── Конкретные поля ──────────────────────────────────────────────────────────

class EncryptedCharField(EncryptedMixin, models.CharField):
    """
    CharField с прозрачным AES-256-CBC шифрованием.
    В БД хранится как TEXT; max_length используется только для Python-валидации.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 500)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Убираем max_length из миграции — поле в БД всегда TEXT
        kwargs.pop('max_length', None)
        return name, path, args, kwargs


class EncryptedTextField(EncryptedMixin, models.TextField):
    """TextField с прозрачным AES-256-CBC шифрованием."""


class EncryptedDateField(EncryptedMixin, models.DateField):
    """
    DateField с прозрачным AES-256-CBC шифрованием.
    Дата сериализуется в ISO-строку 'YYYY-MM-DD' перед шифрованием.
    В БД хранится как TEXT.
    """

    def get_prep_value(self, value):
        """Сериализует date → ISO-строку, затем шифрует."""
        if value is None or value == '':
            return value
        if isinstance(value, str) and value.startswith(_ENCRYPTED_PREFIX):
            return value  # уже зашифровано
        # date/datetime → 'YYYY-MM-DD'
        str_val = value.isoformat() if hasattr(value, 'isoformat') else str(value)
        return _ENCRYPTED_PREFIX + _cipher.encrypt(str_val)

    def _unwrap(self, value):
        """Расшифровывает и возвращает объект date."""
        if value is None or value == '':
            return value
        # Уже объект date
        if hasattr(value, 'year'):
            return value
        if isinstance(value, str) and value.startswith(_ENCRYPTED_PREFIX):
            decrypted = _cipher.decrypt(value[len(_ENCRYPTED_PREFIX):])
        else:
            decrypted = value  # plaintext-строка (до миграции)
        try:
            from datetime import date
            return date.fromisoformat(str(decrypted).strip())
        except (ValueError, TypeError):
            return None

    def to_python(self, value):
        if value is None:
            return value
        if hasattr(value, 'year'):
            return value
        return self._unwrap(value)
