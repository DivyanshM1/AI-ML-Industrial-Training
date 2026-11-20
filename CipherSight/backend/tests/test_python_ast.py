
import ast

import pytest

from app.scanner.python_ast import SecurityScanner


def scan_code(source_code):
    tree = ast.parse(source_code)

    scanner = SecurityScanner(
        source_code=source_code,
        file_path="test_file.py",
    )

    scanner.visit(tree)
    return scanner.findings


def has_rule(findings, rule_id):
    return any(finding["rule_id"] == rule_id for finding in findings)


# Core detection tests

def test_eval_detection():
    assert has_rule(scan_code("result = eval(user_input)"), "CS001")


def test_exec_detection():
    assert has_rule(scan_code("exec(user_input)"), "CS002")


def test_subprocess_shell_true_detection():
    source = """
import subprocess
subprocess.run("dir", shell=True)
"""
    assert has_rule(scan_code(source), "CS003")


def test_clean_code():
    source = """
def add(a, b):
    return a + b

result = add(10, 20)
"""
    assert scan_code(source) == []


def test_syntax_error():
    with pytest.raises(SyntaxError):
        ast.parse("result = eval(")


def test_multiple_vulnerabilities():
    source = """
result = eval(user_input)
exec(user_input)
"""
    findings = scan_code(source)
    rule_ids = {finding["rule_id"] for finding in findings}

    assert {"CS001", "CS002"}.issubset(rule_ids)


def test_pickle_deserialization_detection():
    source = """
import pickle
data = pickle.loads(untrusted_data)
"""
    assert has_rule(scan_code(source), "CS004")


def test_unsafe_yaml_load_detection():
    source = """
import yaml
data = yaml.load(untrusted_data)
"""
    assert has_rule(scan_code(source), "CS005")


def test_safe_yaml_loader_not_flagged():
    source = """
import yaml
data = yaml.load(untrusted_data, Loader=yaml.SafeLoader)
"""
    assert not has_rule(scan_code(source), "CS005")


def test_tls_verification_disabled_detection():
    source = """
import requests
response = requests.get(url, verify=False)
"""
    assert has_rule(scan_code(source), "CS006")


def test_tls_verification_enabled_not_flagged():
    source = """
import requests
response = requests.get(url, verify=True)
"""
    assert not has_rule(scan_code(source), "CS006")


# Import alias detection tests

def test_eval_import_alias():
    source = """
from builtins import eval as evaluate
result = evaluate(user_input)
"""
    assert has_rule(scan_code(source), "CS001")


def test_exec_import_alias():
    source = """
from builtins import exec as execute
execute(user_input)
"""
    assert has_rule(scan_code(source), "CS002")


def test_subprocess_module_alias():
    source = """
import subprocess as sp
sp.run("dir", shell=True)
"""
    assert has_rule(scan_code(source), "CS003")


def test_subprocess_function_alias():
    source = """
from subprocess import run as run_command
run_command("dir", shell=True)
"""
    assert has_rule(scan_code(source), "CS003")


def test_pickle_module_alias():
    source = """
import pickle as p
data = p.loads(untrusted_data)
"""
    assert has_rule(scan_code(source), "CS004")


def test_pickle_function_alias():
    source = """
from pickle import loads as deserialize
data = deserialize(untrusted_data)
"""
    assert has_rule(scan_code(source), "CS004")


def test_yaml_module_alias():
    source = """
import yaml as y
data = y.load(untrusted_data)
"""
    assert has_rule(scan_code(source), "CS005")


def test_yaml_safe_loader_import_alias():
    source = """
from yaml import load, SafeLoader as SL
data = load(untrusted_data, Loader=SL)
"""
    assert not has_rule(scan_code(source), "CS005")


def test_yaml_safe_loader_positional_argument():
    source = """
import yaml
data = yaml.load(untrusted_data, yaml.SafeLoader)
"""
    assert not has_rule(scan_code(source), "CS005")


def test_yaml_unsafe_load_detection():
    source = """
import yaml
data = yaml.unsafe_load(untrusted_data)
"""
    assert has_rule(scan_code(source), "CS005")


def test_requests_module_alias():
    source = """
import requests as req
response = req.get(url, verify=False)
"""
    assert has_rule(scan_code(source), "CS006")


def test_requests_function_alias():
    source = """
from requests import get as fetch
response = fetch(url, verify=False)
"""
    assert has_rule(scan_code(source), "CS006")


def test_httpx_client_verification_disabled():
    source = """
import httpx
client = httpx.Client(verify=False)
"""
    assert has_rule(scan_code(source), "CS006")


def test_httpx_async_client_verification_disabled():
    source = """
import httpx as hx
client = hx.AsyncClient(verify=False)
"""
    assert has_rule(scan_code(source), "CS006")
