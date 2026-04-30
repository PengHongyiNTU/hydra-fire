from __future__ import annotations

from rich.console import Console
from rich.table import Table

from .core.spec import ArgumentField, ConfigSpec, is_exposed_field


def render_decorator_help(
    spec: ConfigSpec,
    console: Console,
    *,
    prog_name: str = "python app.py",
) -> None:
    description = spec.app.description or "Hydra-backed Python entrypoint."
    console.print(f"{spec.app.name} - {description}", markup=False)
    console.print("")
    console.print("[Commands]")
    console.print(f"  {prog_name} [OPTIONS] [HYDRA_OVERRIDES...]", markup=False)
    console.print(f"  {prog_name} --multirun [OPTIONS] [HYDRA_SWEEPS...]", markup=False)
    console.print(f"  {prog_name} fields", markup=False)
    console.print(f"  {prog_name} groups", markup=False)
    console.print(f"  {prog_name} show [OPTIONS] [HYDRA_OVERRIDES...]", markup=False)
    console.print(
        f"  {prog_name} sweep [OPTIONS] [HYDRA_SWEEPS...]  Print Hydra multirun overrides.",
        markup=False,
    )
    console.print(f"  {prog_name} launch", markup=False)
    console.print("")
    console.print("[Examples]")
    for example in _help_examples(spec, prog_name):
        console.print(f"  {example}", markup=False)
    console.print("")
    console.print("[Options]")
    console.print("  -h, --help, help    Show this help.")
    console.print("  -m, --multirun      Print Hydra multirun overrides.")
    if spec.groups:
        _render_help_groups(spec, console)
    if spec.fields:
        _render_help_options(spec, console)
    if spec.presets:
        _render_help_presets(spec, console)
    console.print("")
    console.print("[Hydra Overrides]")
    console.print("  path.to.value=123       Set an existing value.")
    console.print("  +path.to.value=123      Add a new value.")
    console.print("  ++path.to.value=123     Set or add a value.")
    console.print("  ~path.to.value          Remove a value.")
    console.print("")
    console.print(
        "  Advanced Hydra fields are hidden from [Options]. "
        f"Use `{prog_name} fields` or `launch` to discover them.",
        markup=False,
    )


def _render_help_options(spec: ConfigSpec, console: Console) -> None:
    for name, field in spec.fields.items():
        if not is_exposed_field(field):
            continue
        option = f"--{_field_option_name(name, field)}"
        value_hint = "" if field.type == "bool" else " VALUE"
        metadata = f"type={field.type}, path={field.path}"
        if field.default is not None:
            metadata += f", default={field.default}"
        if field.choices:
            metadata += f", choices={','.join(field.choices)}"
        _print_option(console, f"{option}{value_hint}", metadata, field.help)


def _render_help_groups(spec: ConfigSpec, console: Console) -> None:
    for name, group in spec.groups.items():
        if not group.visible:
            continue
        metadata = f"group={group.name}"
        if group.default:
            metadata += f", default={group.default}"
        if group.choices:
            metadata += f", choices={','.join(group.choices)}"
        _print_option(console, f"--{name} VALUE", metadata, group.help)


def _render_help_presets(spec: ConfigSpec, console: Console) -> None:
    choices = ",".join(sorted(spec.presets))
    _print_option(
        console, "--preset VALUE", f"choices={choices}", "Apply a discovered preset in launch mode."
    )


def _print_option(console: Console, option: str, metadata: str, help_text: str) -> None:
    console.print(f"  {option:<24} {metadata}", markup=False)
    if help_text:
        console.print(f"      {help_text}", markup=False)


def _help_examples(spec: ConfigSpec, prog_name: str) -> list[str]:
    option_tokens: list[str] = []
    for name, group in spec.groups.items():
        if not group.visible:
            continue
        value = _sample_choice(group.choices, group.default)
        option_tokens.extend([f"--{name}", value])
        break

    for name, field in spec.fields.items():
        if not is_exposed_field(field):
            continue
        option = f"--{_field_option_name(name, field)}"
        if field.type == "bool":
            if field.default is not True:
                option_tokens.append(option)
        else:
            option_tokens.extend([option, _sample_field_value(field)])
        if len(option_tokens) >= 4:
            break

    examples: list[str] = []
    if option_tokens:
        examples.append(f"{prog_name} {' '.join(option_tokens)}")
        examples.append(f"{prog_name} show {' '.join(option_tokens[:4])}")

    sweep_tokens = _sweep_example_tokens(spec)
    if sweep_tokens:
        examples.append(f"{prog_name} {' '.join(sweep_tokens)}")
        examples.append(f"{prog_name} sweep {' '.join(sweep_tokens)}")

    raw_override = _first_raw_override(spec)
    if raw_override:
        examples.append(f"{prog_name} {raw_override} ++new.value=1")
    examples.append(f"{prog_name} launch")
    return examples


def _field_option_name(name: str, field: ArgumentField) -> str:
    return field.alias or next(iter(field.cli_names), name)


def _sample_choice(choices: list[str], default: str | None) -> str:
    for choice in choices:
        if choice != default:
            return choice
    return default or (choices[0] if choices else "VALUE")


def _sweep_example_tokens(spec: ConfigSpec) -> list[str]:
    tokens: list[str] = []
    for name, group in spec.groups.items():
        if group.visible and len(group.choices) >= 2:
            tokens.extend([f"--{name}", ",".join(group.choices[:2])])
            break

    for name, field in spec.fields.items():
        if not is_exposed_field(field) or not field.sweepable or field.type == "bool":
            continue
        tokens.extend([f"--{_field_option_name(name, field)}", _sample_sweep_values(field)])
        if len(tokens) >= 4:
            break
    return tokens


def _sample_sweep_values(field: ArgumentField) -> str:
    if field.choices and len(field.choices) >= 2:
        return ",".join(field.choices[:2])
    if field.type == "int":
        return "1,2"
    if field.type == "float":
        return "0.001,0.01"
    return "a,b"


def _sample_field_value(field: ArgumentField) -> str:
    if field.choices:
        return _sample_choice(
            field.choices,
            field.default if isinstance(field.default, str) else None,
        )
    if field.default is not None:
        return str(field.default)
    if field.type == "int":
        return "1"
    if field.type == "float":
        return "0.1"
    return "VALUE"


def _first_raw_override(spec: ConfigSpec) -> str:
    for field in spec.fields.values():
        if field.visible and "." in field.path:
            return f"{field.path}={_sample_raw_value(field)}"
    return ""


def _sample_raw_value(field: ArgumentField) -> str:
    if field.type == "bool":
        return "true"
    return _sample_field_value(field)


def render_preset_list(spec: ConfigSpec, console: Console) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Preset")
    table.add_column("Description")
    for name, preset in spec.presets.items():
        table.add_row(name, preset.description)
    console.print(table)


def render_preset_description(spec: ConfigSpec, preset: str, console: Console) -> None:
    card = spec.preset(preset)
    console.print(f"[bold]Preset:[/bold] {preset}")
    if card.description:
        console.print(f"\n[bold]Description:[/bold]\n  {card.description}")
    console.print("\n[bold]Hydra overrides:[/bold]")
    for override in card.overrides:
        console.print(f"  {override}")

    console.print("\n[bold]Fields:[/bold]")
    if spec.fields:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name")
        table.add_column("Path")
        table.add_column("Alias")
        table.add_column("Help")
        for name, field in spec.fields.items():
            table.add_row(name, field.path, field.alias or "", field.help)
        console.print(table)
    else:
        console.print("  No fields defined.")

    if spec.groups:
        console.print("\n[bold]Groups:[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name")
        table.add_column("Choices")
        table.add_column("Help")
        for name, group in spec.groups.items():
            table.add_row(name, ", ".join(group.choices), group.help)
        console.print(table)

    if card.examples:
        console.print("\n[bold]Examples:[/bold]")
        for example in card.examples:
            console.print(f"  {example}")


def render_fields(spec: ConfigSpec, console: Console, *, include_hidden: bool = False) -> None:
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
        row_styles=["", "dim"],
    )
    table.add_column("Name", style="bold", no_wrap=True)
    table.add_column("Option", style="green", no_wrap=True)
    table.add_column("Path", style="magenta", no_wrap=True)
    table.add_column("Level")
    table.add_column("Type")
    table.add_column("Default")
    table.add_column("Help")
    for name, field in spec.fields.items():
        if not include_hidden and not field.visible:
            continue
        option = (
            f"--{field.alias or next(iter(field.cli_names))}" if is_exposed_field(field) else ""
        )
        table.add_row(
            name,
            option,
            field.path,
            field.level,
            field.type,
            "" if field.default is None else str(field.default),
            field.help,
        )
    console.print(table)


def render_groups(spec: ConfigSpec, console: Console, *, include_hidden: bool = False) -> None:
    table = Table(
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
        row_styles=["", "dim"],
    )
    table.add_column("Name", style="bold")
    table.add_column("Option", style="green")
    table.add_column("Choices")
    table.add_column("Default")
    table.add_column("Help")
    for name, group in spec.groups.items():
        if not include_hidden and not group.visible:
            continue
        table.add_row(
            name,
            f"--{name}",
            ", ".join(group.choices),
            group.default or "",
            group.help,
        )
    console.print(table)
