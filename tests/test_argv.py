"""The argv rewriting behind the command line, pinned on whichever Python runs the tests.

Some of it only changes the outcome on Python 3.10 and 3.11, so the parts are tested directly.
"""

from __future__ import annotations

import argparse
from datetime import date

import pytest

from stepdates._argv import Escaped, Mark, Value, late_stop, plain, prepare, settle
from stepdates._cli import _parser


def test_prepare_glues_a_step_to_its_flag() -> None:
    assert prepare(["-s", "-P1M", "--step", "-1 day", "-s"]) == [
        "--step=-P1M",
        "--step=-1 day",
        "-s",
    ]


def test_prepare_wraps_everything_after_the_first_double_dash() -> None:
    prepared = prepare(["2026-01-01", "--", "-s", "--", "x"])
    assert prepared[0] == "2026-01-01"
    assert isinstance(prepared[1], Mark) and prepared[1] != "--"
    assert [type(arg) for arg in prepared[2:]] == [Escaped] * 3
    assert [plain(arg) for arg in prepared[2:]] == ["-s", "--", "x"]
    assert not any(arg.startswith("-") for arg in prepared[2:])


@pytest.mark.parametrize("arg", ["-5", "-1x", "-1_0", "-.5", "-0"])
def test_prepare_wraps_what_starts_like_a_negative_number(arg: str) -> None:
    (prepared,) = prepare([arg])
    assert isinstance(prepared, Escaped) and plain(prepared) == arg


@pytest.mark.parametrize("arg", ["-x", "--bogus", "-", "-.", "--5", "2026-01-01", "-n"])
def test_prepare_leaves_other_arguments_alone(arg: str) -> None:
    assert type(prepare([arg])[0]) is str


def test_plain_returns_the_text_as_written() -> None:
    assert plain(Escaped("-1x")) == "-1x"
    assert plain(Escaped(" -1 ")) == " -1 "
    assert plain(Escaped("")) == ""
    assert plain("x") == "x"


def test_prepare_keeps_spaces_around_a_wrapped_argument() -> None:
    prepared = prepare(["-1 ", "--", " 2026-01-01 ", ""])
    assert [plain(arg) for arg in prepared if not isinstance(arg, Mark)] == [
        "-1 ",
        " 2026-01-01 ",
        "",
    ]


def test_settle_unwraps_values_and_drops_the_mark() -> None:
    args = argparse.Namespace(format=Escaped("-1x"), step="day", count=None)
    extras = settle(args, ["--bogus", Mark(), Escaped("-y")])
    assert (args.format, args.step, args.count) == ("-1x", "day", None)
    assert type(args.format) is str
    assert extras == ["--bogus", Escaped("-y")]


@pytest.mark.parametrize(
    ("extras", "stop", "rest"),
    [
        (["--bogus", "2026-01-03"], "2026-01-03", ["--bogus"]),
        (["-x", "a", "b"], "a", ["-x", "b"]),
        (["--x1", "--x2"], None, ["--x1", "--x2"]),
        ([], None, []),
        (["--bogus", "-5"], "-5", ["--bogus"]),
    ],
)
def test_late_stop_takes_the_first_positional(
    extras: list[str], stop: str | None, rest: list[str]
) -> None:
    assert late_stop(extras) == (stop, rest)


def test_late_stop_takes_a_wrapped_argument() -> None:
    wrapped = Escaped("--inclusive")
    assert late_stop(["--bogus", wrapped]) == (wrapped, ["--bogus"])


def _value(kind: object = None) -> tuple[argparse.ArgumentParser, Value]:
    parser = argparse.ArgumentParser()
    action = parser.add_argument("-v", action=Value, type=kind)  # type: ignore[arg-type]
    assert isinstance(action, Value)
    return parser, action


def test_value_stores_what_it_is_given() -> None:
    parser, action = _value()
    namespace = argparse.Namespace()
    action(parser, namespace, "x")
    assert namespace.v == "x"


@pytest.mark.parametrize("kind", [None, str])
def test_value_stores_an_empty_value_as_empty(kind: object) -> None:
    parser, action = _value(kind)
    namespace = argparse.Namespace()
    action(parser, namespace, "")
    assert namespace.v == "" and type(namespace.v) is str


def test_value_puts_back_a_dropped_double_dash() -> None:
    parser, action = _value()
    namespace = argparse.Namespace()
    action(parser, namespace, [])
    assert namespace.v == "--"


def test_value_reads_a_dropped_double_dash_with_its_type() -> None:
    def refuse(text: str) -> int:
        raise argparse.ArgumentTypeError(f"no number in {text!r}")

    parser, action = _value(refuse)
    with pytest.raises(argparse.ArgumentError, match=r"argument -v: no number in '--'"):
        action(parser, argparse.Namespace(), [])
    parser, action = _value(len)
    namespace = argparse.Namespace()
    action(parser, namespace, [])
    assert namespace.v == 2


def test_take_stop_fills_a_missing_stop_from_the_extras() -> None:
    args = argparse.Namespace(stop=None)
    assert _parser().take_stop(args, ["--bogus", "2026-01-03", "x"]) == ["--bogus", "x"]
    assert args.stop == date(2026, 1, 3)


def test_take_stop_keeps_a_stop_already_read() -> None:
    args = argparse.Namespace(stop=date(2026, 1, 2))
    assert _parser().take_stop(args, ["--bogus", "2026-01-03"]) == ["--bogus", "2026-01-03"]
    assert args.stop == date(2026, 1, 2)


def test_take_stop_reports_a_bad_stop_as_argparse_would(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as stop:
        _parser().take_stop(argparse.Namespace(stop=None), ["--bogus", Escaped("-x")])
    assert stop.value.code == 2
    assert capsys.readouterr().err.splitlines()[-1] == (
        "stepdates: error: argument stop: not an ISO 8601 date or datetime: '-x'"
    )


@pytest.mark.parametrize("unknown", ["--bogus", "-x"])
def test_take_stop_reads_an_empty_stop(unknown: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stop:
        _parser().take_stop(argparse.Namespace(stop=None), [unknown, ""])
    assert stop.value.code == 2
    assert capsys.readouterr().err.splitlines()[-1] == (
        "stepdates: error: argument stop: not an ISO 8601 date or datetime: ''"
    )
