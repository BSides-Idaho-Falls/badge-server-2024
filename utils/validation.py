import random


def dict_types_valid(item: dict, validation_legend: dict) -> bool:
    for k, v in validation_legend.items():
        required = v.get("required", False)
        if required and k not in item:  # Ensure key exists
            return False
        excluded = v.get("excluded", False)
        if excluded and k in item:  # Ensure key does **NOT** exist
            return False
        if k not in item:
            continue  # Already validated via required & excluded
        item_type = v.get("type")
        if not item_type:
            continue  # No typing requirements
        if not isinstance(item[k], item_type):
            return False
    return True


def luhn_checksum(number: str) -> int:
    numbers: list = [c for c in number]
    total_sum: int = 0
    for i, digit in enumerate(reversed(numbers)):
        digit = int(digit)
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total_sum += digit
    checksum_digit = (10 - (total_sum % 10)) % 10
    return checksum_digit


def check_luhn(number: str) -> bool:
    try:
        # Ensure number string is a valid number before passing to checksum
        # Yes, argument is passed in via string and not integer ;)
        int(number)
    except ValueError as _:
        return False
    return luhn_checksum(number) == 0


def generate_luhn(self, size: int) -> str:
    random_number: str = "".join([str(random.randint(0, 9)) for _ in range(size - 1)])
    # 0 is not a typo, it's padding for the checksum
    checksum_digit = self.luhn_checksum(f"{random_number}0")
    luhn = f"{random_number}{checksum_digit}"
    return luhn
