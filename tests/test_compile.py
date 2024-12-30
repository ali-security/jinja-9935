import os
import re

import pytest

from jinja2 import UndefinedError
from jinja2.environment import Environment
from jinja2.loaders import DictLoader

def test_filters_deterministic(tmp_path):
    src = "".join(f"{{{{ {i}|filter{i} }}}}" for i in range(10))
    env = Environment(loader=DictLoader({"foo": src}))
    env.filters.update(dict.fromkeys((f"filter{i}" for i in range(10)), lambda: None))
    env.compile_templates(tmp_path, zip=None)
    name = os.listdir(tmp_path)[0]
    content = (tmp_path / name).read_text("utf8")
    expect = [f"filters['filter{i}']" for i in range(10)]
    found = re.findall(r"filters\['filter\d']", content)
    assert found == expect

def test_import_as_with_context_deterministic(tmp_path):
    src = "\n".join(f'{% import "bar" as bar{i} with context %}' for i in range(10))
    env = Environment(loader=DictLoader({"foo": src}))
    env.compile_templates(tmp_path, zip=None)
    name = os.listdir(tmp_path)[0]
    content = (tmp_path / name).read_text("utf8")
    expect = [f"'bar{i}': " for i in range(10)]
    found = re.findall(r"'bar\d': ", content)[:10]
    assert found == expect

def test_undefined_import_curly_name():
    env = Environment(
        loader=DictLoader(
            {
                "{bad}": "{% from 'macro' import m %}{{ m() }}",
                "macro": "",
            }
        )
    )

    # Must not raise `NameError: 'bad' is not defined`, as that would indicate
    # that `{bad}` is being interpreted as an f-string. It must be escaped.
    with pytest.raises(UndefinedError):
        env.get_template("{bad}").render()
