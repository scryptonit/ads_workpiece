import os
import csv
import subprocess
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

ENCRYPTED_FILE = os.getenv("ENCRYPTED_WALLETS_PATH")

def load_key():
    source = os.getenv("WALLET_SOURCE", "keychain").strip().lower()
    if source == "usb":
        key_path = os.getenv("WALLET_KEY_PATH")
        if not key_path:
            raise EnvironmentError("Environment variable WALLET_KEY_PATH not set.")
        if not os.path.exists(key_path):
            raise FileNotFoundError(f"Key file not found at {key_path}")
        with open(key_path, 'rb') as key_file:
            return key_file.read()
    elif source == "keychain":
        try:
            result = subprocess.run(
                ['security', 'find-generic-password', '-a', 'mishka', '-s', 'uncle_mischa', '-w'],
                capture_output=True,
                text=True,
                check=True
            )
            key = result.stdout.strip().encode()
            return key
        except subprocess.CalledProcessError:
            raise FileNotFoundError('Key not found in macOS Keychain.')

def decrypt_file_to_memory():
    if not ENCRYPTED_FILE or not os.path.exists(ENCRYPTED_FILE):
        raise FileNotFoundError(f'Encrypted file not found: {ENCRYPTED_FILE}')
    key = load_key()
    fernet = Fernet(key)

    with open(ENCRYPTED_FILE, 'rb') as file_in:
        encrypted_data = file_in.read()

    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data.decode('utf-8')

def get_wallets():
    decrypted_text = decrypt_file_to_memory()
    reader = csv.reader(decrypted_text.splitlines())
    header = next(reader, None)

    if header is None or len(header) < 2:
        raise ValueError("Invalid CSV format. Expected at least two columns.")

    wallets = []
    for row in reader:
        if len(row) < 3:
            continue
        address = row[0].strip()
        private_key = row[1].strip()
        seed = row[2].strip()
        wallets.append((address, private_key, seed))
    return wallets

if __name__ == "__main__":
    try:
        decrypted_wallets = get_wallets()
        for addr, privkey, seed in decrypted_wallets:
            logger.info(f"{addr}")
    except Exception as e:
        logger.error(f"{e}")
