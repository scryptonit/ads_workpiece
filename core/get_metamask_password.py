from core.get_wallets_data import load_key
import base64
import hashlib

def derive_password(profile_id: str, length: int = 30) -> str:

    master_key = load_key()
    salt = profile_id.encode('utf-8')
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        master_key,
        salt,
        iterations=100_000,
        dklen=length
    )
    return base64.urlsafe_b64encode(dk).decode('utf-8')

if __name__ == "__main__":
    profile = '432'
    pwd = derive_password(profile)
    print(pwd)
