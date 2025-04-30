from cryptography.fernet import Fernet

key = Fernet.generate_key()

with open('key.key', 'wb') as file:
    file.write(key)

print("Ключ создан и сохранён в key.key")
