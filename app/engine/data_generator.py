from faker import Faker
import uuid

fake = Faker()

def generate_user_data() -> dict:
    """
    Generates unique fake user data for each virtual user.
    Uses uuid4 to guarantee uniqueness every time.
    """
    first = fake.first_name()
    last = fake.last_name()
    unique_id = str(uuid.uuid4()).replace("-", "")[:12]

    return {
        "email": f"lt.{unique_id}@loadtest.dev",
        "full_name": f"{first} {last}",
        "password": fake.password(length=12),
    }