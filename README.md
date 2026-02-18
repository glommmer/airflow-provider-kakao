# Apache Airflow Provider for KakaoTalk

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Airflow](https://img.shields.io/badge/Apache%20Airflow-v3.0%2B-FF4B4B?logo=apacheairflow&logoColor=white)
[![CI](https://github.com/glommmer/airflow-provider-kakao/actions/workflows/ci.yml/badge.svg)](https://github.com/glommmer/airflow-provider-kakao/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/airflow-provider-kakao.svg)](https://badge.fury.io/py/airflow-provider-kakao)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/airflow-provider-kakao)](https://pypi.org/project/airflow-provider-kakao/)

**Apache Airflow Provider for KakaoTalk** allows you to send messages via KakaoTalk API directly from your Airflow DAGs. It supports **"Send to Me"** (default) and **"Send to Friends"** features using the Kakao REST API.

### 🚀 Features

* **Send to Me:** Send notifications (task success/failure alert, reports) to your own KakaoTalk.
* **Send to Friends:** Send messages to specific friends using their UUIDs.
    * *Note:* The provider automatically chunks the recipient list into batches of 5 to comply with API limits.
* **Flexible Message Formats:** Supports simple text messages and complex JSON templates (Feed, List, Commerce, etc.).
* **Token Management:** Automatically refreshes the Access Token using the provided Refresh Token during task execution (Lazy Loading).

### 📦 Installation

You can install the provider via pip:

```bash
pip install apache-airflow-providers-kakao
```

### ⚙️ Connection Setup

To use this provider, you must create a Connection in the Airflow UI.

1.  **Connection Id**: `kakao_default`
2.  **Connection Type**: `kakao` (or `generic`)
3.  **Login**: Kakao Developers **REST API Key** (Client ID)
4.  **Password**: Kakao **Refresh Token**
5.  **Extra** (Optional): If your app uses a Client Secret, provide it in JSON format.
    ```json
    {"client_secret": "YOUR_CLIENT_SECRET"}
    ```

> **⚠️ Prerequisites:**
> * Your Kakao Application must have the "Send to Me" and "Send to Friends" scopes enabled.
> * For "Send to Friends", the target users must be registered as team members in the Kakao Developers console (for testing/dev apps) and must have agreed to the app's permissions.

### 💻 Usage

#### 1. Using the Operator (Recommended)

The `KakaoTalkOperator` is the easiest way to send messages.

```python
from airflow import DAG
from datetime import datetime
from airflow.providers.kakao.operators.kakao import KakaoTalkOperator

with DAG(
    dag_id="kakao_example", 
    start_date=datetime(2026, 1, 1), 
    schedule=None,
) as dag:

    # 1. Simple Text Message (Send to Me)
    send_text = KakaoTalkOperator(
        task_id="send_text",
        text="Hello! The Airflow task has finished successfully. 🚀",
        kakao_conn_id="kakao_default",
    )

    # 2. Send to Friends (UUIDs required)
    send_friend = KakaoTalkOperator(
        task_id="send_friend",
        text="Team Alert: Deployment Started",
        receiver_uuids=["uuid_1", "uuid_2", "uuid_3"],
        kakao_conn_id="kakao_default",
    )

    # 3. Send Custom JSON Template (Feed, Link, etc.)
    # See Kakao Message API docs for template structure
    template = {
        "object_type": "text",
        "text": "Check the detailed report",
        "link": {"web_url": "https://airflow.apache.org"},
    }
    
    send_template = KakaoTalkOperator(
        task_id="send_template",
        kakao_kwargs={"template_object": template},
        kakao_conn_id="kakao_default",
    )
```

#### 2. Using the Hook (Advanced)

You can use `KakaoHook` for custom logic or within a `PythonOperator`.

```python
from airflow.providers.kakao.hooks.kakao import KakaoHook

def my_python_func():
    hook = KakaoHook(kakao_conn_id="kakao_default")
    
    # Send message via Hook
    hook.send_message(
        api_params={"text": "Message sent via KakaoHook."}
    )
```

### ⚠️ Limitations

* **Token Persistence:** This provider **does not persist** the rotated Refresh Token back to the Airflow Metadata Database. It uses the Refresh Token from the connection to get a temporary Access Token for the task.
* **Token Expiry:** You must manually update the Connection with a new Refresh Token before it expires (typically 2 months), or implement a separate pipeline to handle token rotation and DB updates.

---

**Apache Airflow Provider for KakaoTalk**는 Airflow DAG에서 카카오톡 메시지를 전송할 수 있게 해주는 커뮤니티 Provider입니다. 카카오 REST API를 사용하여 **"나에게 보내기"** 및 **"친구에게 보내기"** 기능을 지원합니다.

### 🚀 주요 기능

* **나에게 보내기:** 작업 성공/실패 알림이나 리포트를 내 카카오톡으로 전송합니다.
* **친구에게 보내기:** 지정된 친구(UUID)들에게 메시지를 전송합니다.
    * *참고:* API 제한에 맞춰 수신자 목록을 자동으로 5명씩 나누어 전송합니다.
* **다양한 메시지 포맷:** 단순 텍스트뿐만 아니라 JSON 템플릿(피드, 리스트, 커머스 등)을 지원합니다.
* **토큰 관리:** 작업 실행 시 Refresh Token을 사용하여 Access Token을 자동으로 갱신합니다 (Lazy Loading).

### 📦 설치 방법

pip를 통해 설치할 수 있습니다.

```bash
pip install apache-airflow-providers-kakao
```

### ⚙️ 연결 설정 (Connection Setup)

Airflow UI에서 Connection을 생성해야 합니다.

1.  **Connection Id**: `kakao_default`
2.  **Connection Type**: `kakao` (또는 `generic`)
3.  **Login**: 카카오 디벨로퍼스 **REST API 키** (Client ID)
4.  **Password**: 카카오 **Refresh Token**
5.  **Extra** (선택 사항): Client Secret을 사용하는 경우 JSON으로 입력
    ```json
    {"client_secret": "YOUR_CLIENT_SECRET"}
    ```

> **⚠️ 사전 요구사항:**
> * 카카오 애플리케이션 설정에서 "나에게 보내기" 및 "친구에게 보내기" 권한(Scope)이 활성화되어 있어야 합니다.
> * "친구에게 보내기"를 사용하려면, 수신자가 카카오 디벨로퍼스 팀원으로 등록되어 있어야 하며(테스트 앱의 경우), 앱 권한에 동의한 상태여야 합니다.

### 💻 사용법

#### 1. Operator 사용 (권장)

`KakaoTalkOperator`를 사용하여 간단하게 메시지를 보낼 수 있습니다.

```python
from airflow import DAG
from datetime import datetime
from airflow.providers.kakao.operators.kakao import KakaoTalkOperator

with DAG(
    dag_id="kakao_example", 
    start_date=datetime(2026, 1, 1), 
    schedule=None,
) as dag:

    # 1. 단순 텍스트 메시지 (나에게 보내기)
    send_text = KakaoTalkOperator(
        task_id="send_text",
        text="안녕하세요! Airflow 작업이 성공적으로 완료되었습니다. 🚀",
        kakao_conn_id="kakao_default",
    )

    # 2. 친구에게 보내기 (UUID 필요)
    send_friend = KakaoTalkOperator(
        task_id="send_friend",
        text="팀원 알림: 배포가 시작되었습니다.",
        receiver_uuids=["uuid_1", "uuid_2", "uuid_3"],
        kakao_conn_id="kakao_default",
    )

    # 3. 커스텀 JSON 템플릿 보내기 (피드, 링크 등)
    # 템플릿 구조는 카카오 메시지 API 문서를 참고하세요.
    template = {
        "object_type": "text",
        "text": "자세한 리포트 확인하기",
        "link": {"web_url": "https://airflow.apache.org"},
    }
    
    send_template = KakaoTalkOperator(
        task_id="send_template",
        kakao_kwargs={"template_object": template},
        kakao_conn_id="kakao_default",
    )
```

#### 2. Hook 사용 (고급)

`PythonOperator` 내부나 커스텀 로직에서 `KakaoHook`을 직접 사용할 수 있습니다.

```python
from airflow.providers.kakao.hooks.kakao import KakaoHook

def my_python_func():
    hook = KakaoHook(kakao_conn_id="kakao_default")
    
    # Hook을 이용한 메시지 전송
    hook.send_message(
        api_params={"text": "KakaoHook을 통해 전송된 메시지입니다."}
    )
```

### ⚠️ 제약 사항

* **토큰 영구 저장 미지원:** 이 Provider는 갱신된 Refresh Token을 Airflow 메타데이터 DB에 **저장하지 않습니다**. 연결(Connection)에 저장된 Refresh Token을 사용하여 일회성 Access Token을 발급받는 방식입니다.
* **토큰 만료 관리:** Refresh Token이 만료(보통 2달)되기 전에 Connection 정보를 수동으로 업데이트하거나, 별도의 토큰 갱신 파이프라인을 구축해야 합니다.