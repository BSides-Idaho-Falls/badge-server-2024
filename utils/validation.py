
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
