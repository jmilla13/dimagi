import json
import random
import string
import sys
from urllib.parse import urljoin

import requests


def random_email():
    first = random.choice([
        "alex", "maria", "sam", "jordan", "taylor", "casey", "riley", "jamie", "drew", "elliot"
    ])
    last = random.choice([
        "chen", "oliveira", "patel", "kim", "nguyen", "brown", "garcia", "singh", "mendez", "thomas"
    ])
    number = random.randint(10, 99)
    return f"{first}.{last}{number}@example.com"


def random_location():
    cities = [
        "London",
        "Paris",
        "Berlin",
        "Tokyo",
        "Sydney",
        "Cape Town",
        "Toronto",
        "Mexico City",
        "Nairobi",
        "Reykjavik",
        "Buenos Aires",
        "Seoul",
        "Mumbai",
        "Cairo",
        "Lagos",
        "Stockholm",
        "Oslo",
        "Dublin",
        "Lisbon",
        "Singapore",
    ]
    return random.choice(cities)


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    endpoint = urljoin(base_url.rstrip("/") + "/", "api/locations/")

    for i in range(10):
        payload = {
            "email": random_email(),
            "location": random_location(),
        }
        try:
            response = requests.post(endpoint, json=payload, timeout=20)
            print(f"{i + 1}. {payload['email']} -> {payload['location']} -> {response.status_code}")
            if response.status_code >= 400:
                print(response.text)
        except Exception as exc:
            print(f"{i + 1}. {payload['email']} -> {payload['location']} -> ERROR: {exc}")


if __name__ == "__main__":
    main()
