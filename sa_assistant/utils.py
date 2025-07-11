import os
import yaml
from .context import AssistantContext


def name_to_email(name: str) -> str:
    return name.replace(" ", ".").lower() + "@stackadapt.com"


def email_to_name(email: str) -> str:
    parts = []
    for part in email.split("@")[0].split("."):
        parts.append(part.capitalize())
    return " ".join(parts)


def load_config_and_setup_env() -> tuple[dict, AssistantContext]:
    """
    Load configuration from config.yaml and set up environment variables.
    This function sets the OPENAI_API_KEY environment variable and returns
    both the raw config dict and the AssistantContext instance.

    """
    config = yaml.load(open("config.yaml"), Loader=yaml.Loader)

    # Set the OpenAI API key environment variable
    os.environ["OPENAI_API_KEY"] = config["openai_api_key"]

    # Create the context instance
    context = AssistantContext(**config)

    return config, context
