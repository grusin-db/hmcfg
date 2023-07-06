import pytest
import hmcfg

def test_pytest():
  assert True

def test_package_import():
  assert hmcfg.__version__ is not None