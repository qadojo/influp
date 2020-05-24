import sys
from typing import Set

from influp.uri import UriMerger, UriFilter, parse_uri_from_log, parse_status_from_log, parse_timestamp_from_log

_merge_file_name = "merge.influp"
_filter_file_name = "filter.influp"

_influx_measurement_name = "access"

_usage = """Parses access logs of Common Log format to influx file protocol.

Usage:
    cat access.log | influp > influx.line.format.file
    cat access.log | influp links > unique.links.file

If current directory contains "merge.influp" file it will be used to merge URIs by glob.
Matching URIs will be merged to glob.
Example merge.influp file:
    GET /some/uri/*/with/path/params
    POST /other/uri/*
    
If current directory contains "filter.influp" file it will be used to filter URIs by glob.
Only matching URIs from access log will be processed.
Example filter.influp file:
    GET /some/uri/*/with/path/params
    POST /other/uri/*

Common Log format example:
    127.0.0.1 - - [06/Dec/2019:13:40:27 +0300] "GET /nginx_status HTTP/1.1" 422 81 "-" "curl/7.29.0"
"""


def main():
    try:
        uri_filter = UriFilter.from_file(_filter_file_name)
        merger = UriMerger.from_file(_merge_file_name)

        if len(sys.argv) == 2:
            if sys.argv[1] == "links":
                extract_unique_links(uri_filter, merger)
                return

        elif len(sys.argv) == 1:
            convert_logs_to_influx(uri_filter, merger)
            return

        print(_usage)
        sys.exit(1)
    except KeyboardInterrupt:
        pass


def extract_unique_links(uri_filter: UriFilter, merger: UriMerger) -> None:
    unique_uris: Set[str] = set()

    line: str
    for line in sys.stdin.readlines():
        line = line.strip()

        method, uri = parse_uri_from_log(line)

        if not uri_filter.allows(method, uri):
            continue

        method, uri = merger.merge(method, uri)

        uri_spec = method + " " + uri

        if uri_spec not in unique_uris:
            unique_uris.add(uri_spec)
            sys.stdout.write(uri_spec)
            sys.stdout.write("\n")


def convert_logs_to_influx(uri_filter: UriFilter, merger: UriMerger):
    sys.stdout.write("# DDL\n")
    sys.stdout.write("# CREATE DATABASE requests\n\n")
    sys.stdout.write("# DML\n")
    sys.stdout.write("# CONTEXT-DATABASE: requests\n\n")

    line: str
    for line in sys.stdin.readlines():
        line = line.strip()

        method, uri = parse_uri_from_log(line)

        if not uri_filter.allows(method, uri):
            continue

        method, uri = merger.merge(method, uri)

        status = parse_status_from_log(line)

        timestamp = parse_timestamp_from_log(line)

        sys.stdout.write(f'{_influx_measurement_name},method={method},status={status},uri={uri} value=1 {timestamp}\n')
