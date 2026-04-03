"""
AES Encryption/Decryption utility for I4C integration
Mode: CBC, Padding: PKCS7, Key: Hex, Encoding: Base64
"""
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import hashlib


class I4CEncryption:
    """I4C compliant AES encryption/decryption"""
    
    def __init__(self, hex_key: str):
        """
        Initialize with hex key
        Args:
            hex_key: 32-character hex string (128-bit) or 64-character (256-bit)
        """
        # Convert hex key to bytes
        self.key = bytes.fromhex(hex_key)
        # Ensure key is valid length (16, 24, or 32 bytes for AES)
        if len(self.key) not in [16, 24, 32]:
            raise ValueError(f"Invalid key length: {len(self.key)}. Must be 16, 24, or 32 bytes.")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext using AES-CBC with PKCS7 padding
        Returns base64 encoded encrypted string with IV prepended
        """
        # Generate random IV (16 bytes for AES)
        iv = get_random_bytes(16)
        
        # Create cipher
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        
        # Pad and encrypt
        padded_data = pad(plaintext.encode('utf-8'), AES.block_size, style='pkcs7')
        encrypted = cipher.encrypt(padded_data)
        
        # Combine IV + encrypted data and base64 encode
        result = base64.b64encode(iv + encrypted).decode('utf-8')
        return result
    
    def encrypt_payload(self, payload_data: dict) -> str:
        """
        Encrypt a dictionary payload for I4C API
        Converts dict to JSON string then encrypts
        """
        import json
        json_payload = json.dumps(payload_data, default=str)
        return self.encrypt(json_payload)
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt base64 encoded ciphertext
        Expects IV prepended to encrypted data
        """
        try:
            # Base64 decode
            encrypted_data = base64.b64decode(ciphertext)
            
            # Extract IV (first 16 bytes) and encrypted content
            iv = encrypted_data[:16]
            encrypted = encrypted_data[16:]
            
            # Create cipher and decrypt
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(encrypted)
            
            # Unpad
            unpadded = unpad(decrypted, AES.block_size, style='pkcs7')
            
            return unpadded.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")


def get_encryption_key() -> str:
    """Get or generate encryption key for I4C"""
    # In production, this should come from secure environment/config
    # Using a fixed 32-byte hex key (256-bit AES)
    return "0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF"


# Global encryption instance
_encryption = None

def get_i4c_encryption() -> I4CEncryption:
    """Get singleton I4C encryption instance"""
    global _encryption
    if _encryption is None:
        _encryption = I4CEncryption(get_encryption_key())
    return _encryption
