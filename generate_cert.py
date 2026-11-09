from datetime import datetime, timedelta, timezone
from ipaddress import ip_address

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


# Створення приватного ключа
key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# Дані сертифіката
name = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "UA"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "VideoInspector"),
    x509.NameAttribute(NameOID.COMMON_NAME, "192.168.0.110"),
])

# Сертифікат для локального комп'ютера
cert = (
    x509.CertificateBuilder()
    .subject_name(name)
    .issuer_name(name)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.now(timezone.utc))
    .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.IPAddress(ip_address("192.168.0.110")),
            x509.DNSName("localhost"),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

# Збереження приватного ключа
with open("key.pem", "wb") as file:
    file.write(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

# Збереження сертифіката
with open("cert.pem", "wb") as file:
    file.write(cert.public_bytes(serialization.Encoding.PEM))

print("SSL-сертифікат успішно створено.")