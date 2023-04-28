import unittest
from unittest.mock import MagicMock, patch

from jose import JOSEError, ExpiredSignatureError
from Cryptodome.Cipher import AES

from common.encrypt import (
    Jwt,
    AESUtil,
    HashUtil,
    SignAuth,
    HashUtilB64,
    PasswordUtil,
)


class TestAESUtil(unittest.TestCase):
    def setUp(self):
        self.aes_key = AESUtil.generate_key()
        self.style = "pkcs7"
        self.mode = AES.MODE_ECB

    def test_generate_key(self):
        key = AESUtil.generate_key()
        self.assertIsInstance(key, str)
        self.assertGreaterEqual(len(key), 43)

    def test_encrypt_data(self):
        plain_text = "hello, world!"
        aes = AESUtil(self.aes_key, style=self.style, mode=self.mode)
        cipher_text = aes.encrypt_data(plain_text)
        self.assertIsInstance(cipher_text, str)
        self.assertNotEqual(plain_text, cipher_text)

    def test_encrypt_and_decrypt(self):
        aes = AESUtil(self.aes_key, style=self.style, mode=self.mode)
        plain_text = "hello, world!"
        cipher_text = aes.encrypt_data(plain_text)
        decrypt_plain_text = aes.decrypt_data(cipher_text)
        self.assertEqual(plain_text, decrypt_plain_text)


# class TestRSAUtil(unittest.TestCase):
#     def setUp(self):
#         self.pub_key_path = f"{local_configs.PROJECT.BASE_DIR.absolute()}
#         /tests/unit/component/rsa/rsa_pub.pem"
#         self.private_key_path = f"{local_configs.PROJECT.BASE_DIR.absolute()}
#         /tests/unit/component/rsa/rsa_private.pfx"
#         self.password = "test_password"
#         self.rsa = RSAUtil(self.pub_key_path, self.private_key_path, self.password)

#     def test_encrypt_decrypt(self):
#         plain_text = "Hello World! This is a test message."
#         encrypted_text = self.rsa.encrypt(plain_text)
#         # decrypted_text = self.rsa.decrypt(encrypted_text)
#         # self.assertEqual(decrypted_text, plain_text)

#     def test_sign_verify(self):
#         message = "This is a test message for signing and verifying."
#         signature = self.rsa.sign(message)
#         self.assertTrue(self.rsa.verify(signature, message))

#     def test_encrypt_decrypt_long_text(self):
#         plain_text = "A" * 1000
#         encrypted_text = self.rsa.encrypt(plain_text)
#         decrypted_text = self.rsa.decrypt(encrypted_text)
#         self.assertEqual(decrypted_text, plain_text)

#     def test_sign_verify_long_text(self):
#         message = "A" * 1000
#         signature = self.rsa.sign(message)
#         self.assertTrue(self.rsa.verify(signature, message))

#     def test_decrypt_invalid_input(self):
#         encrypted_text = "invalid_input"
#         with self.assertRaises(ValueError):
#             self.rsa.decrypt(encrypted_text)

#     def test_verify_invalid_input(self):
#         signature = "invalid_input"
#         message = "This is a test message for signing and verifying."
#         with self.assertRaises(ValueError):
#             self.rsa.verify(signature, message)

#     def tearDown(self):
#         del self.rsa


class TestHashUtil(unittest.TestCase):
    def test_md5_encode(self):
        self.assertEqual(
            HashUtil.md5_encode("test"), "098f6bcd4621d373cade4e832627b4f6"
        )
        self.assertEqual(
            HashUtil.md5_encode("hello world"),
            "5eb63bbbe01eeed093cb22bb8f5acdc3",
        )
        self.assertEqual(
            HashUtil.md5_encode(""),
            "d41d8cd98f00b204e9800998ecf8427e",
        )

    def test_hmac_sha256_encode(self):
        self.assertEqual(
            HashUtil.hmac_sha256_encode("key", "The quick brown fox"),
            "203d1e5cedd2d18f8c5a3beff0bd9c1ebcb97097dfcb288c46b00c9227fde2c0",
        )
        self.assertEqual(
            HashUtil.hmac_sha256_encode("secret", "message"),
            "8b5f48702995c1598c573db1e21866a9b825d4a794d169d7060a03605796360b",
        )
        self.assertEqual(
            HashUtil.hmac_sha256_encode("", ""),
            "b613679a0814d9ec772f95d778c35fc5ff1697c493715653c6c712144292c5ad",
        )

    def test_sha1_encode(self):
        self.assertEqual(
            HashUtil.sha1_encode("test"),
            "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
        )
        self.assertEqual(
            HashUtil.sha1_encode("hello world"),
            "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed",
        )
        self.assertEqual(
            HashUtil.sha1_encode(""),
            "da39a3ee5e6b4b0d3255bfef95601890afd80709",
        )


class TestHashUtilB64(unittest.TestCase):
    def test_md5_encode_b64(self):
        # 测试字符串 "hello"
        result = HashUtilB64.md5_encode_b64("hello")
        self.assertEqual(result, "XUFAKrxLKna5cZ2REBfFkg==")

        # 测试空字符串
        result = HashUtilB64.md5_encode_b64("")
        self.assertEqual(result, "1B2M2Y8AsgTpgAmY7PhCfg==")

    def test_hmac_sha256_encode_b64(self):
        # 测试字符串 "hello"，密钥为 "world"
        result = HashUtilB64.hmac_sha256_encode_b64("world", "hello")
        self.assertEqual(
            result, "PPp27xSTfBwOpRn4/AV6gPzQSnQg+Oi80KdWfCcuAHs="
        )

        # 测试空字符串和密钥
        result = HashUtilB64.hmac_sha256_encode_b64("", "")
        self.assertEqual(
            result, "thNnmggU2ex3L5XXeMNfxf8Wl8STcVZTxscSFEKSxa0="
        )

    def test_sha1_encode_b64(self):
        # 测试字符串 "hello"
        result = HashUtilB64.sha1_encode_b64("hello")
        self.assertEqual(result, "qvTGHdzF6KLavt4PO0gs2a6pQ00=")

        # 测试空字符串
        result = HashUtilB64.sha1_encode_b64("")
        self.assertEqual(result, "2jmj7l5rSw0yVb/vlWAYkK/YBwk=")


class TestSignAuth(unittest.TestCase):
    def test_verify_returns_true_when_sign_matches_generated_sign(self):
        # Arrange
        private_key = "test_private_key"
        sign = "test_sign"
        data_str = "test_data_str"

        # Mock generate_sign
        mock_generate_sign = MagicMock(return_value=sign)

        # Create instance and patch generate_sign
        sign_auth = SignAuth(private_key)
        sign_auth.generate_sign = mock_generate_sign

        # Act
        result = sign_auth.verify(sign, data_str)

        # Assert
        self.assertTrue(result)
        mock_generate_sign.assert_called_once_with(data_str)

    def test_verify_returns_false_when_sign_does_not_match_generated_sign(
        self,
    ):
        # Arrange
        private_key = "test_private_key"
        sign = "test_sign"
        data_str = "test_data_str"

        # Mock generate_sign
        mock_generate_sign = MagicMock(return_value="another_sign")

        # Create instance and patch generate_sign
        sign_auth = SignAuth(private_key)
        sign_auth.generate_sign = mock_generate_sign

        # Act
        result = sign_auth.verify(sign, data_str)

        # Assert
        self.assertFalse(result)
        mock_generate_sign.assert_called_once_with(data_str)

    def test_generate_sign_returns_valid_signature(self):
        # Arrange
        private_key = "test_private_key"
        data_str = "test_data_str"
        expected_sign = HashUtilB64.hmac_sha256_encode_b64(
            private_key, data_str
        )

        # Create instance
        sign_auth = SignAuth(private_key)

        # Act
        sign = sign_auth.generate_sign(data_str)

        # Assert
        self.assertEqual(sign, expected_sign)


class TestPasswordUtil(unittest.TestCase):
    def test_verify_password(self):
        # 测试验证正确密码
        plain_password = "test_password"
        hashed_password = PasswordUtil.get_password_hash(plain_password)
        self.assertTrue(
            PasswordUtil.verify_password(plain_password, hashed_password)
        )

        # 测试验证错误密码
        wrong_password = "wrong_password"
        self.assertFalse(
            PasswordUtil.verify_password(wrong_password, hashed_password)
        )

    def test_get_password_hash(self):
        # 测试生成哈希值
        plain_password = "test_password"
        hashed_password = PasswordUtil.get_password_hash(plain_password)
        self.assertTrue(hashed_password.startswith("$2b$"))


class TestJwt(unittest.TestCase):
    def setUp(self):
        self.secret = "mysecret"
        self.jwt_util = Jwt(self.secret)

    def test_get_jwt_valid(self):
        payload = {"id": 1, "username": "testuser"}
        jwt_token = self.jwt_util.get_jwt(payload)
        self.assertIsNotNone(jwt_token)
        self.assertIsInstance(jwt_token, str)

    def test_decode_valid(self):
        payload = {"id": 1, "username": "testuser"}
        jwt_token = self.jwt_util.get_jwt(payload)
        decoded_payload = self.jwt_util.decode(jwt_token)
        self.assertIsNotNone(decoded_payload)
        self.assertIsInstance(decoded_payload, dict)
        self.assertEqual(decoded_payload["id"], payload["id"])
        self.assertEqual(decoded_payload["username"], payload["username"])

    def test_decode_invalid_signature(self):
        payload = {"id": 1, "username": "testuser"}
        jwt_token = self.jwt_util.get_jwt(payload)
        from jose import jwt

        jwt.decode

        with patch("jose.jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.side_effect = JOSEError
            with self.assertRaises(JOSEError):
                self.jwt_util.decode(jwt_token)

    def test_decode_expired_signature(self):
        payload = {"id": 1, "username": "testuser"}
        jwt_token = self.jwt_util.get_jwt(payload)

        with patch("jose.jwt.decode") as mock_jwt_decode:
            mock_jwt_decode.side_effect = ExpiredSignatureError
            with self.assertRaises(ExpiredSignatureError):
                self.jwt_util.decode(jwt_token)
