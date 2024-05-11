from typing import List, Optional


def solution_to_lucky_numbers(solution: Optional[List[List[int]]]):
    if not solution:
        return "0"
    numbers: List[str] = []
    for item in solution:
        for subitem in item:
            numbers.append(str(subitem))
    return " ".join(numbers)
