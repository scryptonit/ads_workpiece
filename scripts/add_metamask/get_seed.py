import os
from loguru import logger
from core.get_wallets_data import get_wallets

def load_profiles(file_name="profiles.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, file_name)
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def load_addresses(file_name="addresses.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, file_name)
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def build_profile_to_seed_map(profiles_file="profiles.txt", addresses_file="addresses.txt"):
    profiles = load_profiles(profiles_file)
    addresses = load_addresses(addresses_file)
    wallets = get_wallets()

    if len(profiles) != len(addresses):
        raise ValueError(f"profiles({len(profiles)}) != addresses({len(addresses)})")

    seed_map = {addr.lower(): (addr, seed) for addr, _, seed in wallets}

    profile_data = {}
    for pid, addr in zip(profiles, addresses):
        item = seed_map.get(addr.lower())
        if item:
            profile_data[pid] = item
        else:
            logger.warning(f"No seed found for address {addr}, profile {pid}")

    return profile_data

def get_address_and_seed_for_profile(profile_id):
    mapping = build_profile_to_seed_map()
    result = mapping.get(str(profile_id))
    if result is None:
        raise KeyError(f"No seed found for profile '{profile_id}'")
    return result
