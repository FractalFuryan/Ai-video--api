def test_api_key_header_name():
    from api.middleware.auth import API_KEY_NAME

    assert API_KEY_NAME == "X-API-Key"
