import requests
import pytest

from httpie import ExitStatus
from utils import TestEnvironment, http, httpbin, HTTP_OK


class TestExitStatus:
    def test_ok_response_exits_0(self):
        r = http('GET', httpbin('/status/200'))
        assert HTTP_OK in r
        assert r.exit_status == ExitStatus.OK

    def test_error_response_exits_0_without_check_status(self):
        r = http('GET', httpbin('/status/500'))
        assert 'HTTP/1.1 500' in r
        assert r.exit_status == ExitStatus.OK
        assert not r.stderr

    @pytest.mark.skipif(
        tuple(map(int, requests.__version__.split('.'))) < (2, 3, 0),
        reason='timeout broken in requests prior v2.3.0 (#185)'
    )
    def test_timeout_exit_status(self):

        r = http('--timeout=0.5', 'GET', httpbin('/delay/1'),
                 error_exit_ok=True)
        assert r.exit_status == ExitStatus.ERROR_TIMEOUT

    def test_3xx_check_status_exits_3_and_stderr_when_stdout_redirected(self):
        env = TestEnvironment(stdout_isatty=False)
        r = http('--check-status', '--headers', 'GET', httpbin('/status/301'),
                 env=env, error_exit_ok=True)
        assert 'HTTP/1.1 301' in r
        assert r.exit_status == ExitStatus.ERROR_HTTP_3XX
        assert '301 moved permanently' in r.stderr.lower()

    @pytest.mark.skipif(
        requests.__version__ == '0.13.6',
        reason='Redirects with prefetch=False are broken in Requests 0.13.6')
    def test_3xx_check_status_redirects_allowed_exits_0(self):
        r = http('--check-status', '--follow', 'GET', httpbin('/status/301'),
                 error_exit_ok=True)
        # The redirect will be followed so 200 is expected.
        assert 'HTTP/1.1 200 OK' in r
        assert r.exit_status == ExitStatus.OK

    def test_4xx_check_status_exits_4(self):
        r = http('--check-status', 'GET', httpbin('/status/401'),
                 error_exit_ok=True)
        assert 'HTTP/1.1 401' in r
        assert r.exit_status == ExitStatus.ERROR_HTTP_4XX
        # Also stderr should be empty since stdout isn't redirected.
        assert not r.stderr

    def test_5xx_check_status_exits_5(self):
        r = http('--check-status', 'GET', httpbin('/status/500'),
                 error_exit_ok=True)
        assert 'HTTP/1.1 500' in r
        assert r.exit_status == ExitStatus.ERROR_HTTP_5XX
