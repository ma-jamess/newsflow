from pathlib import Path


def test_project_environment_created_instead_of_foreign_install(tmp_path, monkeypatch):
    import run
    monkeypatch.setattr(run, 'ROOT', tmp_path)
    monkeypatch.setattr(run.sys, 'prefix', str(tmp_path / 'foreign-venv'))
    monkeypatch.setattr(run.importlib.util, 'find_spec', lambda name: None)
    calls = []
    monkeypatch.setattr(run.subprocess, 'run', lambda command, **kw: calls.append(command))
    monkeypatch.setattr(run.subprocess, 'call', lambda command, **kw: calls.append(command) or 0)
    run.choose_environment(False)
    assert calls[0][1:3] == ['-m', 'venv']
    assert calls[0][3] == str(tmp_path / '.venv')
    assert str(calls[1][0]).startswith(str(tmp_path / '.venv'))
