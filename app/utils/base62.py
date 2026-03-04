"""
Утилиты для генерации коротких кодов
Base62 encoding (0-9, a-z, A-Z) для компактных URL
"""
import random
import string


# Base62 алфавит: цифры + строчные + заглавные буквы
BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase


def generate_short_code(length: int = 6) -> str:
    """
    Генерация случайного короткого кода используя Base62
    
    Args:
        length: Длина генерируемого кода (по умолчанию 6)
        
    Returns:
        str: Случайный код из Base62 символов
        
    Example:
        >>> generate_short_code(6)
        'aB3xY9'
    """
    return ''.join(random.choices(BASE62_ALPHABET, k=length))


def encode_base62(num: int) -> str:
    """
    Кодирование числа в Base62 строку
    Полезно для генерации кода на основе ID записи
    
    Args:
        num: Число для кодирования
        
    Returns:
        str: Base62 представление числа
        
    Example:
        >>> encode_base62(12345)
        '3d7'
    """
    if num == 0:
        return BASE62_ALPHABET[0]
    
    result = []
    base = len(BASE62_ALPHABET)
    
    while num > 0:
        remainder = num % base
        result.append(BASE62_ALPHABET[remainder])
        num //= base
    
    return ''.join(reversed(result))


def decode_base62(code: str) -> int:
    """
    Декодирование Base62 строки обратно в число
    
    Args:
        code: Base62 строка
        
    Returns:
        int: Декодированное число
        
    Example:
        >>> decode_base62('3d7')
        12345
    """
    base = len(BASE62_ALPHABET)
    result = 0
    
    for char in code:
        result = result * base + BASE62_ALPHABET.index(char)
    
    return result


