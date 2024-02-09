from typing import Callable

from result import Result

from .emails import main as get_emails
from .zuerichunbezahlbar_ch import main as get_zuerichunbezahlbar_ch

# Add new sources here
sources: list[Callable[[], Result]] = [
    get_emails,
    get_zuerichunbezahlbar_ch
]


def main():
    for source in sources:
        result = source()
        if result.is_err():
            print(result.err())


if __name__ == "__main__":
    main()
