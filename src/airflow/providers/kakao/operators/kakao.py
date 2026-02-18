"""Operator for KakaoTalk."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Any, List, Dict

from airflow.providers.common.compat.sdk import AirflowException, BaseOperator
from airflow.providers.kakao.hooks.kakao import KakaoHook

if TYPE_CHECKING:
    from airflow.providers.common.compat.sdk import Context


class KakaoTalkOperator(BaseOperator):
    """
    This operator allows you to send messages to KakaoTalk using the Kakao REST API.

    It supports two modes of operation:
    1. Send to Me: Sends a message to the authenticated user (default behavior).
    2. Send to Friends: Sends a message to specific friends if 'receiver_uuids' is provided.

    It accepts the Kakao Token directly or via an Airflow Connection.
    If both are supplied, the 'token' parameter is given precedence.

    .. seealso::
        For more information on the KakaoTalk API, visit:
        https://developers.kakao.com/docs/latest/en/message/rest-api

    :param kakao_conn_id: The Airflow connection ID. The connection should contain the REST API Key in 'Login'
        and the Refresh Token in 'Password'.
    :param token: (Optional) Kakao Access Token.
    :param text: The message text to be sent. (templated)
    :param receiver_uuids: (Optional) A list of Kakao UUIDs for the target friends.
        If provided, the message is sent to these users. (templated)
    :param kakao_kwargs: (Optional) Extra arguments to be passed to the Kakao client.
        Common keys include 'web_url' for links or 'template_object' for custom JSON templates. (templated)
    """

    template_fields: Sequence[str] = ("text", "receiver_uuids", "kakao_kwargs")
    ui_color = "#FEE500"

    def __init__(
        self,
        *,
        kakao_conn_id: str = "kakao_default",
        token: str | None = None,
        text: Optional[str] = None,
        receiver_uuids: Optional[List[str]] = None,
        kakao_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        self.token = token
        self.receiver_uuids = receiver_uuids
        self.kakao_kwargs = kakao_kwargs or {}
        self.text = text

        if kakao_conn_id is None:
            raise AirflowException("No valid Kakao connection id supplied.")

        self.kakao_conn_id = kakao_conn_id

        super().__init__(**kwargs)

    def execute(self, context: Context) -> None:
        """Call the KakaoHook to send the Kakao message."""
        if self.text is not None:
            self.kakao_kwargs["text"] = self.text

        kakao_hook = KakaoHook(
            kakao_conn_id=self.kakao_conn_id,
            token=self.token,
        )
        kakao_hook.send_message(
            receiver_uuids=self.receiver_uuids,
            api_params=self.kakao_kwargs,
        )
