import random
import string

_letters = string.ascii_letters + string.digits


def random_alfanum(n: int) -> str:
    return "".join(random.choice(_letters) for _ in range(n))
