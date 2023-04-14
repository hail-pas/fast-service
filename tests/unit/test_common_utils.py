from common.utils import generate_random_string


def test_generate_random_string():
    length = 8
    assert len(generate_random_string(length)) == length
