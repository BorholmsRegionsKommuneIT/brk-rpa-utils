import secrets
import string


def generate_new_password(char_count: int):
    alphabet = string.ascii_letters + string.digits
    password = []

    # Ensure at least one letter and one digit
    password.append(secrets.choice(string.ascii_letters))
    password.append(secrets.choice(string.digits))

    # Fill the rest of the length with random characters
    for _ in range(char_count - 2):
        password.append(secrets.choice(alphabet))

    # Shuffle the password to mix letters and digits
    secrets.SystemRandom().shuffle(password)

    return "".join(password)
