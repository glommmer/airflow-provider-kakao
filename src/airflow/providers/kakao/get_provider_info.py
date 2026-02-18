def get_provider_info():
    return {
        "package-name": "apache-airflow-providers-kakao",
        "name": "KakaoTalk",
        "description": "A KakaoTalk provider for Apache Airflow.",
        "versions": ["0.0.1"],
        "connection-types": [
            {
                "connection-type": "kakao",
                "hook-class-name": "airflow.providers.kakao.hooks.kakao.KakaoHook"
            }
        ],
    }
