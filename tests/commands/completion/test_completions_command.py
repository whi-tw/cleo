from __future__ import annotations

import os

from typing import TYPE_CHECKING

import pytest

from cleo._compat import WINDOWS
from cleo.application import Application
from cleo.testers.command_tester import CommandTester
from tests.commands.completion.fixtures.command_with_colons import CommandWithColons
from tests.commands.completion.fixtures.command_with_space_in_name import SpacedCommand
from tests.commands.completion.fixtures.hello_command import HelloCommand


if TYPE_CHECKING:
    from pytest_mock import MockerFixture


app = Application()
app.add(HelloCommand())
app.add(CommandWithColons())
app.add(SpacedCommand())


def test_invalid_shell() -> None:
    command = app.find("completions")
    tester = CommandTester(command)

    with pytest.raises(ValueError):
        tester.execute("pomodoro")


@pytest.mark.skipif(WINDOWS, reason="Only test linux shells")
@pytest.mark.parametrize(
    "function_name, should_raise",
    [("some_function", True), ("_some_function", False)],
)
@pytest.mark.parametrize(
    "shell, expected_if_not_raise",
    [
        ("bash", "complete -o default -F {function_name} /path/to/script"),
        ("zsh", "compdef {function_name} /path/to/script"),
        ("fish", "function __fish{function_name}_no_subcommand"),
    ],
)
def test_function_name_flag(
    mocker: MockerFixture,
    function_name: str,
    should_raise: bool,
    shell: str,
    expected_if_not_raise: str,
) -> None:
    mocker.patch(
        "cleo.io.inputs.string_input.StringInput.script_name",
        new_callable=mocker.PropertyMock,
        return_value="/path/to/script",
    )

    command = app.find("completions")
    tester = CommandTester(command)

    if should_raise:
        with pytest.raises(
            ValueError, match="The function name must start with an underscore"
        ):
            tester.execute(f"{shell} --function-name={function_name}")
    else:
        tester.execute(f"{shell} --function-name={function_name}")
        assert (
            expected_if_not_raise.format(function_name=function_name)
            in tester.io.fetch_output()
        )


@pytest.mark.skipif(WINDOWS, reason="Only test linux shells")
@pytest.mark.parametrize(
    "script_path, output_fixture_filename",
    [
        ("/path/to/my/script", "bash.txt"),
        ("/path/with space/to/my/script", "bash_with_space_in_script_name.txt"),
    ],
)
def test_bash(
    mocker: MockerFixture, script_path: str, output_fixture_filename: str
) -> None:
    mocker.patch(
        "cleo.io.inputs.string_input.StringInput.script_name",
        new_callable=mocker.PropertyMock,
        return_value=script_path,
    )
    mocker.patch(
        "cleo.commands.completions_command.CompletionsCommand._generate_function_name",
        return_value="_my_function",
    )

    command = app.find("completions")
    tester = CommandTester(command)
    tester.execute("bash")

    fixture_path = os.path.join(
        os.path.dirname(__file__), "fixtures", output_fixture_filename
    )

    with open(fixture_path) as f:
        expected = f.read()

    assert expected == tester.io.fetch_output().replace("\r\n", "\n")


@pytest.mark.skipif(WINDOWS, reason="Only test linux shells")
@pytest.mark.parametrize(
    "script_path, output_fixture_filename",
    [
        ("/path/to/my/script", "zsh.txt"),
        ("/path/with space/to/my/script", "zsh_with_space_in_script_name.txt"),
    ],
)
def test_zsh(
    mocker: MockerFixture, script_path: str, output_fixture_filename: str
) -> None:
    mocker.patch(
        "cleo.io.inputs.string_input.StringInput.script_name",
        new_callable=mocker.PropertyMock,
        return_value=script_path,
    )
    mocker.patch(
        "cleo.commands.completions_command.CompletionsCommand._generate_function_name",
        return_value="_my_function",
    )

    command = app.find("completions")
    tester = CommandTester(command)
    tester.execute("zsh")

    with open(
        os.path.join(os.path.dirname(__file__), "fixtures", output_fixture_filename)
    ) as f:
        expected = f.read()

    assert expected == tester.io.fetch_output().replace("\r\n", "\n")


@pytest.mark.skipif(WINDOWS, reason="Only test linux shells")
def test_fish(mocker: MockerFixture) -> None:
    mocker.patch(
        "cleo.io.inputs.string_input.StringInput.script_name",
        new_callable=mocker.PropertyMock,
        return_value="/path/to/my/script",
    )
    mocker.patch(
        "cleo.commands.completions_command.CompletionsCommand._generate_function_name",
        return_value="_my_function",
    )

    command = app.find("completions")
    tester = CommandTester(command)
    tester.execute("fish")

    with open(os.path.join(os.path.dirname(__file__), "fixtures", "fish.txt")) as f:
        expected = f.read()

    assert expected == tester.io.fetch_output().replace("\r\n", "\n")
