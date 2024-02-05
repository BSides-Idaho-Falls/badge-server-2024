from typing import List, Optional


def extract_vault_location(construction: List[dict]) -> Optional[List[int]]:
    for item in construction:
        material_type: str = item["material_type"]
        if material_type == "Vault":
            return item["location"]
    return None


def extract_locations(construction: List[dict]) -> List[List[int]]:
    grid: List[List[int]] = []
    for item in construction:
        material_type: str = item["material_type"]
        if material_type == "Vault":
            continue
        grid.append(item["location"])
    return grid


def deconstruct_house(construction: List[dict]):
    vault_location: List[int] = extract_vault_location(construction)
    materials: List[List[int]] = extract_locations(construction)


