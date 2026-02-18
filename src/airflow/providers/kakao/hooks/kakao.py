"""Hook for KakaoTalk."""

from __future__ import annotations

import requests
import json
from typing import Any, Dict, List
from functools import cached_property

from airflow.providers.common.compat.sdk import AirflowException, BaseHook


class KakaoHook(BaseHook):
    """
    Interact with KakaoTalk API to send messages to the authenticated user ("Send to Me")
    or to specific friends ("Send to Friends").

    This hook utilizes a 'Lazy Loading' pattern via '@cached_property'.
    Network requests for token retrieval are only made when 'send_message' is explicitly called,
    ensuring that DAG parsing and initialization remain lightweight and fail-safe.

    Token Management Strategy:
        This hook uses the Refresh Token stored in the Airflow Connection to obtain a temporary
        Access Token for the current task execution.

    .. warning::
        This hook does not persist new Refresh Tokens back to the Airflow Connection database.
        It assumes that a separate maintenance DAG or external process handles the
        lifecycle and rotation of the Refresh Token stored in the Connection.

    It accepts both the Kakao Access/Refresh Token directly or via an Airflow Connection.
    If both are supplied, the direct 'token' parameter takes precedence.

    .. note::
        To send messages to friends, the friends must also have agreed to the app's permissions
        and be registered as team members in the Kakao Developers console (for non-business apps).

    Connection Details:

    The default connection ID is 'kakao_default'.
    Configure the connection in Airflow as follows:

    - Conn Type: 'kakao' (or 'generic')
    - Login: REST API Key (Client ID)
    - Password: Refresh Token
    - Extra: JSON object containing optional secrets
        > '{"client_secret": "YOUR_CLIENT_SECRET"}' (if enabled in Kakao Developers)

    Examples:
    .. code-block:: python

        # 1. Create hook using the default connection 'kakao_default'
        kakao_hook = KakaoHook()

        # 2. Send a simple text message to yourself (Send to Me)
        kakao_hook.send_message(
            api_params={"text": "Hello, Airflow!"}
        )

        # 3. Send a message with a custom URL to yourself
        kakao_hook.send_message(
            api_params={
                "text": "Task Failed",
                "web_url": "https://airflow.apache.org"
            }
        )

        # 4. Send a message to specific friends (Send to Friends)
        # The hook automatically chunks the list into batches of 5.
        kakao_hook.send_message(
            receiver_uuids=["uuid1", "uuid2", "uuid3"],
            api_params={"text": "Team Announcement: Deployment Complete"}
        )

        # 5. Send a complex JSON template (Feed, List, Commerce, etc.)
        template = {
            "object_type": "feed",
            "content": {
                "title": "Daily Report",
                "description": "ETL Process Finished",
                "image_url": "http://image.url",
                "link": {"web_url": "http://google.com"}
            }
        }
        kakao_hook.send_message(
            api_params={"template_object": template}
        )

    :param kakao_conn_id: Connection ID that contains the Kakao REST API Key and Refresh Token.
    :param token: (Optional) Kakao Access Token. If provided, it overrides the token from the connection.
    """

    conn_name_attr = "kakao_conn_id"
    default_conn_name = "kakao_default"
    conn_type = "kakao"
    hook_name = "Kakao"

    def __init__(
        self,
        kakao_conn_id: str | None = default_conn_name,
        token: str | None = None,
    ) -> None:
        super().__init__()
        self._token = token
        self.kakao_conn_id = kakao_conn_id
        self.token_url = "https://kauth.kakao.com/oauth/token"
        self.send_me_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        self.send_friend_url = (
            "https://kapi.kakao.com/v1/api/talk/friends/message/default/send"
        )

    @cached_property
    def token(self) -> str:
        """Return the Kakao REST API token."""
        if self._token:
            return self._token

        if not self.kakao_conn_id:
            raise AirflowException("No valid Kakao connection supplied.")

        conn = self.get_connection(self.kakao_conn_id)
        client_id = conn.login
        refresh_token = conn.password
        client_secret = conn.extra_dejson.get("client_secret")

        if not client_id or not refresh_token:
            raise AirflowException(
                "REST API Key (Login) or Refresh Token (Password) is missing in the Connection."
            )

        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
        data = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        }

        if client_secret:
            data["client_secret"] = client_secret

        try:
            self.log.info("Refreshing Kakao Access Token...")
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()

            tokens = response.json()
            new_access_token = tokens.get("access_token")
            new_refresh_token = tokens.get("refresh_token")

            if not new_access_token:
                raise AirflowException(
                    "Token Refresh Failed: No access_token in response"
                )

            if new_refresh_token:
                self.log.warning("Refresh Token Rotated.")

            return new_access_token

        except Exception as e:
            self.log.error(f"Failed to refresh token: {e}")
            raise AirflowException(f"Kakao Token Refresh Error: {e}")

    def send_message(
        self,
        receiver_uuids: List[str] | None = None,
        api_params: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Send a message to the authenticated user ("Send to Me") or specific friends ("Send to Friends").

        If 'receiver_uuids' is provided, the message is sent to those friends (automatically chunked by 5).
        Otherwise, the message is sent to the current authenticated user.

        :param receiver_uuids: (Optional) List of target users' UUIDs.
        :param api_params: Dictionary containing message content parameters.
            It must contain 'text' (for simple text messages) or 'template_object' (for custom JSON templates).
            Optional keys: 'web_url', 'mobile_web_url'.
        """
        current_token = self.token
        default_url = "http://localhost:8080"
        headers = {
            "Authorization": f"Bearer {current_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        if "template_object" in api_params:
            payload = api_params["template_object"]
            if isinstance(payload, str):
                payload = json.loads(payload)
        elif "text" in api_params:
            text = api_params.get("text")
            web_url = api_params.get("web_url", default_url)
            mobile_web_url = api_params.get("mobile_web_url", web_url)
            payload = {
                "object_type": "text",
                "text": text,
                "link": {
                    "web_url": web_url,
                    "mobile_web_url": mobile_web_url,
                },
            }
        else:
            raise AirflowException(
                "message_args must contain 'text' or 'template_object'."
            )

        results = []

        try:
            if receiver_uuids:
                chunk_size = 5
                total_receivers = len(receiver_uuids)

                chunks = [
                    receiver_uuids[i : i + chunk_size]
                    for i in range(0, total_receivers, chunk_size)
                ]

                self.log.info(
                    f"Sending message to {total_receivers} friends (Total {len(chunks)} batches)..."
                )

                for idx, chunk in enumerate(chunks):
                    self.log.info(
                        f"Processing batch {idx + 1}/{len(chunks)} (Count: {len(chunk)})"
                    )

                    data = {
                        "receiver_uuids": json.dumps(chunk),
                        "template_object": json.dumps(payload),
                    }

                    response = requests.post(
                        self.send_friend_url, headers=headers, data=data
                    )
                    response.raise_for_status()

                    result = response.json()
                    results.append(result)

                    failed_uuids = result.get("failure_info", [])
                    if failed_uuids:
                        self.log.warning(
                            f"Batch {idx + 1} - Some messages failed to send: {failed_uuids}"
                        )
            else:
                data = {"template_object": json.dumps(payload)}

                response = requests.post(self.send_me_url, headers=headers, data=data)
                response.raise_for_status()
                results.append(response.json())

            self.log.info("All requests completed successfully.")
            return results

        except requests.exceptions.HTTPError as e:
            self.log.error(f"HTTP Error: {e.response.text}")
            raise AirflowException(f"KakaoTalk Send Error: {e}")
