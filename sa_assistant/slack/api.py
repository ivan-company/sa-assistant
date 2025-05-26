from typing import List
from slack_sdk import WebClient
from .models import SlackChannel, SlackChat


class SlackAPI:

    def __init__(self, api_token):
        self.api_token = api_token
        self.client = WebClient(token=self.api_token)

    def fetch_channels(self) -> List[SlackChannel]:
        results = []

        channels_response = self.client.conversations_list(
            types="public_channel,private_channel"
        )

        for channel in channels_response["channels"]:
            results.append(SlackChannel(
                id=channel["id"],
                name=channel["name"],
                is_private=channel.get("is_private", False))
            )

        return results

    def fetch_chats(self) -> List[SlackChat]:
        results = []
        next_cursor = None
        while True:
            response = self.client.users_list(limit=200, cursor=next_cursor)

            for user in response["members"]:
                results.append(SlackChat(
                    id=user["id"],
                    real_name=user.get("real_name", user.get(
                        "profile", {}).get("real_name", "")),
                    name=user.get("name")
                ))

            if not response.get('response_metadata').get('next_cursor'):
                break

            next_cursor = response["response_metadata"]["next_cursor"]

        return results

    def send_message(self, channel_id: str, message: str):
        response = self.client.chat_postMessage(
            channel=channel_id,
            text=message
        )

        return response
