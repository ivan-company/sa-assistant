def name_to_email(name: str) -> str:
    return name.replace(" ", ".").lower() + "@stackadapt.com"


def email_to_name(email: str) -> str:
    parts = []
    for part in email.split("@")[0].split("."):
        parts.append(part.capitalize())
    return " ".join(parts)
