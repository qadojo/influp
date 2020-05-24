from dataclasses import dataclass, field
from datetime import datetime
from fnmatch import fnmatch
from typing import List, Tuple


@dataclass
class UriMerger:
    merges: List[Tuple[str, str]] = field(default_factory=lambda: [])

    @staticmethod
    def from_file(rules_file_path) -> "UriMerger":
        merger = UriMerger()
        merge_rules = []

        try:
            with open(rules_file_path) as merge_f:
                for line in merge_f:
                    merge_rules.append(line.strip())
        except FileNotFoundError:
            pass

        merger.read_rules(merge_rules)
        return merger

    def read_rules(self, merge_rules: List[str]) -> None:
        for merge_rule in merge_rules:
            method, uri = merge_rule.split()
            self.merges.append((method, uri))

    def merge(self, method: str, uri: str) -> Tuple[str, str]:
        for method_rule, uri_rule in self.merges:
            if method != method_rule:
                continue

            if fnmatch(uri, uri_rule):
                return method, uri_rule

        return method, uri


@dataclass
class UriFilter:
    includes: List[Tuple[str, str]] = field(default_factory=lambda: [])

    @staticmethod
    def from_file(rules_file_path) -> "UriFilter":
        uri_filter = UriFilter()
        filter_rules = []

        try:
            with open(rules_file_path) as rules_f:
                for line in rules_f:
                    filter_rules.append(line.strip())
        except FileNotFoundError:
            pass

        uri_filter.read_rules(filter_rules)
        return uri_filter

    def read_rules(self, filter_rules: List[str]) -> None:
        for filter_rule in filter_rules:
            method, uri = filter_rule.split()
            self.includes.append((method, uri))

    def allows(self, method: str, uri: str) -> bool:
        for method_rule, uri_rule in self.includes:
            if method != method_rule:
                continue

            if fnmatch(uri, uri_rule):
                return True

        return False


def normalize_uri(uri: str) -> str:
    query_start = uri.find("?")
    if query_start != -1:
        uri = uri[:query_start]

    if len(uri) > 1 and uri[-1] == "/":
        uri = uri[:-1]

    return uri


def parse_uri_from_log(line: str) -> Tuple[str, str]:
    uri_start = line.find('"') + 1
    uri_end = line.find('"', uri_start)

    uri_parts = line[uri_start:uri_end].strip().split()
    if len(uri_parts) != 3:
        return "", ""

    method, uri, _ = uri_parts

    uri = normalize_uri(uri)

    return method, uri


_example_uri = '127.0.0.1 - - [06/Dec/2019:13:40:27 +0300] "GET /nginx_status HTTP/1.1" 422 81 "-" "curl/7.29.0"'


def parse_status_from_log(line: str) -> str:
    second_quote = line.find('"', line.find('"') + 1) + 2
    next_space = line.find(' ', second_quote)

    return line[second_quote:next_space]


def parse_timestamp_from_log(line: str) -> str:
    first_bracket = line.find("[")
    second_bracket = line.find("]", first_bracket)

    dt_str = line[first_bracket + 1:second_bracket]
    dt = datetime.strptime(dt_str, "%d/%b/%Y:%H:%M:%S %z")

    return str(int(dt.timestamp()))
