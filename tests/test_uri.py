from unittest import TestCase

from influp.uri import normalize_uri, UriMerger, UriFilter, parse_uri_from_log, parse_status_from_log, \
    parse_timestamp_from_log

_example_uri = '127.0.0.1 - - [06/Dec/2019:13:40:27 +0300] "GET /nginx_status HTTP/1.1" 422 81 "-" "curl/7.29.0"'


class TestUriLib(TestCase):

    def test_normalize_query_params(self):
        assert normalize_uri("/a/b/c?x=1&y=2") == "/a/b/c"

    def test_strip_trailing_slash(self):
        assert normalize_uri("/a/b/c/") == "/a/b/c"

    def test_root_path(self):
        assert normalize_uri("/") == "/"

    def test_parse_uri(self):
        assert parse_uri_from_log(_example_uri) == ("GET", "/nginx_status")

    def test_parse_status(self):
        assert parse_status_from_log(_example_uri) == "422"

    def test_parse_timestamp(self):
        assert parse_timestamp_from_log(_example_uri) == "1575628827"


class TestUriMerger(TestCase):
    def test_read_merge_spec(self):
        uri_merger = UriMerger()
        uri_merger.read_rules(["POST /a/b/c",
                               "GET /a/*/d"])

        method, uri = uri_merger.merge("GET", "/a/123/d")

        assert method == "GET"
        assert uri == "/a/*/d"


class TestUriFilter(TestCase):
    def test_read_merge_spec(self):
        uri_filter = UriFilter()
        uri_filter.read_rules(["POST /a/b/c/*"])

        assert uri_filter.allows("POST", "/a/b/c/123")
        assert not uri_filter.allows("GET", "/a/b/c/d")
