import unittest
from unittest import mock
from airflow.providers.kakao.hooks.kakao import KakaoHook


class TestKakaoHook(unittest.TestCase):
    def setUp(self):
        # Hook 인스턴스 생성 (테스트용 Connection ID 사용)
        self.hook = KakaoHook(kakao_conn_id='test_kakao_conn')

    @mock.patch('airflow.providers.kakao.hooks.kakao.KakaoHook.get_connection')
    @mock.patch('airflow.providers.kakao.hooks.kakao.requests.post')
    def test_send_message_to_me_success(self, mock_post, mock_get_conn):
        """
        [시나리오]
        1. '나에게 보내기' 테스트
        2. Connection에서 Refresh Token을 가져와서 Access Token을 갱신해야 함 (요청 1)
        3. 갱신된 Access Token으로 메시지를 전송해야 함 (요청 2)
        """

        # --- 1. Mock: Airflow Connection 설정 ---
        mock_conn = mock.Mock()
        mock_conn.login = 'dummy_client_id'  # REST API Key
        mock_conn.password = 'dummy_refresh_token'  # Refresh Token
        mock_conn.extra_dejson = {'client_secret': 'dummy_secret'}
        mock_get_conn.return_value = mock_conn

        # --- 2. Mock: API 응답 설정 (순서대로) ---
        # 첫 번째 호출: 토큰 갱신 (Refresh Token -> Access Token)
        mock_response_token = mock.Mock()
        mock_response_token.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token'
        }
        mock_response_token.raise_for_status.return_value = None

        # 두 번째 호출: 메시지 전송 (나에게 보내기)
        mock_response_send = mock.Mock()
        mock_response_send.json.return_value = {'result_code': 0}
        mock_response_send.raise_for_status.return_value = None

        # side_effect를 사용해 호출 순서대로 다른 응답을 주도록 설정
        mock_post.side_effect = [mock_response_token, mock_response_send]

        # --- 3. 실행 (api_params 사용) ---
        # 실제 코드: send_message(api_params={"text": "..."})
        result = self.hook.send_message(
            api_params={"text": "테스트 메시지입니다."}
        )

        # --- 4. 검증 (Assertion) ---
        # (1) 리턴 타입은 리스트여야 합니다.
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['result_code'], 0)

        # (2) requests.post가 총 2번 호출되었는지 확인
        self.assertEqual(mock_post.call_count, 2)

        # (3) 첫 번째 호출 (토큰 갱신) 검증
        first_call_args = mock_post.call_args_list[0]
        self.assertEqual(first_call_args[0][0], self.hook.token_url)  # URL 확인
        self.assertIn('grant_type', first_call_args[1]['data'])  # Data 확인

        # (4) 두 번째 호출 (메시지 전송) 검증
        second_call_args = mock_post.call_args_list[1]
        self.assertEqual(second_call_args[0][0], self.hook.send_me_url)  # URL 확인
        self.assertIn('template_object', second_call_args[1]['data'])  # Payload 확인

    @mock.patch('airflow.providers.kakao.hooks.kakao.KakaoHook.get_connection')
    @mock.patch('airflow.providers.kakao.hooks.kakao.requests.post')
    def test_send_message_missing_text(self, mock_post, mock_get_conn):
        """
        [시나리오]
        api_params에 'text'나 'template_object'가 없으면 AirflowException이 발생해야 함
        """
        # Connection Mock은 필요 (Token 갱신 시도 전이나 후에 실패할 수 있음)
        mock_conn = mock.Mock()
        mock_conn.login = 'id'
        mock_conn.password = 'pw'
        mock_conn.extra_dejson = {}
        mock_get_conn.return_value = mock_conn

        # 토큰 갱신은 성공한다고 가정
        mock_response_token = mock.Mock()
        mock_response_token.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_response_token

        # 실행 및 예외 검증
        from airflow.exceptions import AirflowException

        with self.assertRaises(AirflowException) as context:
            self.hook.send_message(api_params={})  # 빈 딕셔너리 전달

        self.assertIn("must contain 'text' or 'template_object'", str(context.exception))