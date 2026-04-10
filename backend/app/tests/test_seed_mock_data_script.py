import pytest

from app.scripts.seed_mock_data import parse_args


def test_parse_args_default_flags_do_not_require_reset(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "sys.argv",
        ["seed_mock_data.py"],
    )

    cfg = parse_args()

    assert cfg.reset_mock is False
    assert cfg.with_taxonomy is True
    assert cfg.with_edge_cases is True


@pytest.mark.parametrize(
    "flag",
    [
        "--no-with-taxonomy",
        "--no-with-edge-cases",
    ],
)
def test_parse_args_requires_reset_when_disabling_flags(
    monkeypatch: pytest.MonkeyPatch, flag: str
):
    monkeypatch.setattr(
        "sys.argv",
        ["seed_mock_data.py", flag],
    )

    with pytest.raises(
        SystemExit,
        match=(
            "--reset-mock is required when using --no-with-taxonomy or --no-with-edge-cases"
        ),
    ):
        parse_args()


@pytest.mark.parametrize(
    "flag",
    [
        "--no-with-taxonomy",
        "--no-with-edge-cases",
    ],
)
def test_parse_args_allows_disabling_flags_with_reset(
    monkeypatch: pytest.MonkeyPatch, flag: str
):
    monkeypatch.setattr(
        "sys.argv",
        ["seed_mock_data.py", flag, "--reset-mock"],
    )

    cfg = parse_args()

    assert cfg.reset_mock is True
