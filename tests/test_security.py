import asyncio
from app.security import is_safe_public_url


def test_blocks_loopback_urls():
    assert not asyncio.run(is_safe_public_url('http://127.0.0.1/admin'))
    assert not asyncio.run(is_safe_public_url('http://localhost:8080'))


def test_blocks_private_literal():
    assert not asyncio.run(is_safe_public_url('http://10.0.0.5/x'))
    assert not asyncio.run(is_safe_public_url('http://169.254.169.254/latest/meta-data'))
