import random
import string
import tiktoken


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def generate_random_string(length, possible_characters=string.ascii_letters + string.digits) -> str:
    return ''.join(random.choices(possible_characters, k=length))


def generate_random_ip() -> str:
    return ".".join(str(random.randint(0, 255)) for _ in range(4))


def generate_random_digit_string(length) -> str:
    return ''.join(random.choices('0123456789', k=length))
