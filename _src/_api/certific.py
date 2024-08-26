import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

def extract_pfx_to_pem_crt_key(pfx_file, password, pem_file, crt_file, key_file):
    try:
        with open(pfx_file, 'rb') as f:
            pfx_data = f.read()

        pfx = pkcs12.load_key_and_certificates(pfx_data, password.encode(), default_backend())

        private_key = pfx[0]
        certificate = pfx[1]

        # Save private key to PEM file
        with open(key_file, 'wb') as keyf:
            keyf.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Save certificate to CRT file
        with open(crt_file, 'wb') as crt:
            crt.write(certificate.public_bytes(
                encoding=serialization.Encoding.PEM
            ))

        # Save certificate to PEM file
        with open(pem_file, 'wb') as pemf:
            pemf.write(certificate.public_bytes(
                encoding=serialization.Encoding.PEM
            ))

        print("Extraction successful")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def extract_pfx(pfx_path,password,export_path=os.path.join('static','cert')):
    if not os.path.exists(export_path):
        os.makedirs(export_path)
    extract_pfx_to_pem_crt_key(pfx_path, password,os.path.join(export_path,'cert.pem'),os.path.join(export_path,'cert.crt'),os.path.join(export_path,'cert.key'))
    return 0
