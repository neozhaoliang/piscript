"""Render complete EPS files without depending on a TeX installation."""

import pytest

from piscript.PiScript import PiScript
from piscript.Arc import circle
from piscript.PSExec import PSExec


def test_eps_output_with_context_manager(tmp_path):
    output = tmp_path / "sample.eps"
    with PiScript(PSExec(), str(output), 100, 100) as ps:
        ps.newpath()
        circle(ps, (50, 50), 30)
        ps.stroke()
    text = output.read_text(encoding="latin-1")
    assert text.startswith("%!PS-Adobe")
    assert "%%BoundingBox: 0 0 100 100" in text
    assert text.count(" curveto") >= 4
    assert text.rstrip().endswith("%%EOF")


def test_repeated_finish_is_safe(tmp_path):
    output = tmp_path / "again.ps"
    renderer = PiScript(PSExec(), str(output), 20, 20)
    renderer.finish()
    before = output.read_bytes()
    renderer.finish()
    assert output.read_bytes() == before


def test_context_exception_does_not_create_output(tmp_path):
    output = tmp_path / "broken.eps"
    with pytest.raises(RuntimeError, match="failure"):
        with PiScript(PSExec(), str(output), 20, 20):
            raise RuntimeError("failure")
    assert not output.exists()
