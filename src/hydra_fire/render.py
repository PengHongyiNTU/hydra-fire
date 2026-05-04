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
    console.print(f"  {prog_name} recipes", markup=False)
    console.print(f"  {prog_name} show [OPTIONS] [HYDRA_OVERRIDES...]", markup=False)
    console.print(
        f"  {prog_name} sweep [OPTIONS] [HYDRA_SWEEPS...]  Print Hydra multirun overrides.",
        markup=False,
    )
    console.print(
        f"  {prog_name} explain <field|group|group=choice|preset>  Show details",
        markup=False,
    )
    console.print(
        f"  {prog_name} suggest <name>   Fuzzy-find a field, group, or preset",
        markup=False,
    )
    console.print(f"  {prog_name} launch", markup=False)
    console.print("")
    console.print("[Examples]")
    for example in _help_examples(spec, prog_name):
        console.print(f"  {example}", markup=False)
    console.print("")
    if spec.run_modes:
        _render_help_run_modes(spec, console, prog_name=prog_name)
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


def _render_help_run_modes(spec: ConfigSpec, console: Console, *, prog_name: str = "app") -> None:
    console.print("[Launch Modes]")
    console.print("  Choose one:", markup=False)
    for mode in spec.run_modes:
        required_flags = " ".join(f"--{r}" for r in mode.requires)
        optional_flags = " ".join(f"[--{o}]" for o in mode.optional)
        parts = [required_flags, optional_flags] if optional_flags else [required_flags]
        console.print(f"    {' '.join(p for p in parts if p)}", markup=False)
    console.print("")


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
        metadata = f"group={group.hydra_group}"
        if group.default:
            metadata += f", default={group.default}"
        if group.choices:
            metadata += f", choices={','.join(group.choices)}"
        cli_flag = next(iter(group.cli_names), name)
        _print_option(console, f"--{cli_flag} VALUE", metadata, group.help)


def _render_help_presets(spec: ConfigSpec, console: Console) -> None:
    public_name = spec.preset_config.public_name
    choices = ",".join(sorted(spec.presets))
    _print_option(
        console,
        f"--{public_name} VALUE",
        f"choices={choices}",
        f"Apply a {public_name} in launch mode.",
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
        cli_flag = next(iter(group.cli_names), name)
        option_tokens.extend([f"--{cli_flag}", value])
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
            cli_flag = next(iter(group.cli_names), name)
            tokens.extend([f"--{cli_flag}", ",".join(group.choices[:2])])
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
    public_name = spec.preset_config.public_name.capitalize()
    table = Table(show_header=True, header_style="bold")
    table.add_column(public_name)
    table.add_column("Description")
    for name, preset in spec.presets.items():
        table.add_row(name, preset.description)
    console.print(table)


def render_preset_description(spec: ConfigSpec, preset: str, console: Console) -> None:
    card = spec.preset(preset)
    public_name = spec.preset_config.public_name.capitalize()
    console.print(f"[bold]{public_name}:[/bold] {preset}")
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


def render_fields(
    spec: ConfigSpec,
    console: Console,
    *,
    include_hidden: bool = False,
    level: str | None = None,
    search: str | None = None,
) -> None:
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
        if level is not None and field.level != level:
            continue
        if search is not None:
            needle = search.lower()
            if not (
                needle in name.lower()
                or needle in field.path.lower()
                or needle in field.help.lower()
            ):
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
    table.add_column("Target", style="magenta")
    table.add_column("Choices")
    table.add_column("Default")
    table.add_column("Help")
    for name, group in spec.groups.items():
        if not include_hidden and not group.visible:
            continue
        cli_flag = next(iter(group.cli_names), name)
        table.add_row(
            name,
            f"--{cli_flag}",
            group.hydra_group,
            ", ".join(group.choices),
            group.default or "",
            group.help,
        )
    console.print(table)


def _render_explain_field(field: ArgumentField, console: Console) -> None:
    level_color = {
        "core": "green",
        "common": "cyan",
        "advanced": "yellow",
        "debug": "dim",
        "raw": "dim",
    }.get(field.level, "white")

    console.print(f"[bold]Field:[/bold] [cyan]{field.path}[/cyan]")
    if field.alias:
        console.print(f"  CLI flag : [green]--{field.alias}[/green]")
    console.print(f"  Type     : {field.type}")
    console.print(f"  Default  : {field.default!r}")
    console.print(f"  Level    : [{level_color}]{field.level}[/{level_color}]")
    if field.choices:
        console.print(f"  Choices  : {', '.join(field.choices)}")
    if field.help:
        console.print(f"  Help     : {field.help}")

    if field.level in ("advanced", "debug"):
        console.print(
            f"\n[dim]This field is [{level_color}]{field.level}[/{level_color}][dim] — "
            f"use raw Hydra override syntax: "
            f"[cyan]{field.path}=<value>[/cyan][/dim]"
        )
    elif field.alias:
        console.print(f"\n[dim]Usage: [cyan]--{field.alias} <value>[/cyan][/dim]")


def render_explain(
    spec: ConfigSpec,
    target: str,
    console: Console,
    *,
    config_path: str | None = None,
    config_name: str = "config",
    base_path: str | None = None,
) -> None:
    """Explain a field, group, group=choice, or preset by name.

    Accepted forms:
      explain lr              # field by path or alias (strips leading --)
      explain --lr            # same, dashes stripped
      explain model           # group by name
      explain model=small     # group choice → show resolved config
      explain my_preset       # preset by name
    """
    from difflib import get_close_matches

    # Strip leading dashes so --lr and lr both work
    key = target.lstrip("-")

    # --- group=choice ---
    if "=" in key:
        group_name, choice = key.split("=", 1)
        group = spec.groups.get(group_name)
        console.print(f"[bold]Group:[/bold] {group_name} = {choice}")
        if group:
            console.print(f"  Hydra path: [cyan]{group.hydra_group}={choice}[/cyan]")
            if group.choices:
                console.print(f"  Choices:    {', '.join(group.choices)}")
        if config_path:
            try:
                from .compose import compose_config, to_yaml

                cfg = compose_config(
                    config_path,
                    config_name,
                    [f"{group.hydra_group if group else group_name}={choice}"],
                    base_path=base_path,
                )
                console.print("\n[bold]Resolved config:[/bold]")
                console.print(to_yaml(cfg))
            except Exception as exc:
                console.print(f"[yellow]Could not compose config: {exc}[/yellow]")
        return

    # --- field by path or alias ---
    field: ArgumentField | None = spec.fields.get(key)
    if field is None:
        for f in spec.fields.values():
            if f.alias == key:
                field = f
                break
    if field is not None:
        _render_explain_field(field, console)
        return

    # --- group by name ---
    group = spec.groups.get(key)
    if group is not None:
        cli_flag = next(iter(group.cli_names), group.name)
        console.print(f"[bold]Group:[/bold] {group.name}")
        console.print(f"  CLI flag  : [green]--{cli_flag}[/green]")
        console.print(f"  Hydra path: [cyan]{group.hydra_group}[/cyan]")
        if group.choices:
            console.print(f"  Choices   : {', '.join(group.choices)}")
        if group.default:
            console.print(f"  Default   : {group.default}")
        if group.help:
            console.print(f"  Help      : {group.help}")
        console.print(f"\n[dim]Usage: [cyan]--{cli_flag} <choice>[/cyan][/dim]")
        return

    # --- preset by name ---
    if key in spec.presets:
        render_preset_description(spec, key, console)
        return

    # --- not found ---
    candidates: list[str] = (
        list(spec.fields)
        + [f.alias for f in spec.fields.values() if f.alias]
        + list(spec.groups)
        + list(spec.presets)
    )
    matches = get_close_matches(key, sorted(set(candidates)), n=3, cutoff=0.4)
    msg = f"[red]Nothing found for '{target}'.[/red]"
    if matches:
        msg += f"  Did you mean: {', '.join(matches)}?"
    console.print(msg)


def render_suggest(spec: ConfigSpec, name: str, console: Console) -> None:
    """Suggest close matches for a partial flag name."""
    from difflib import get_close_matches

    candidates: list[str] = []
    candidates.extend(spec.fields.keys())
    candidates.extend(f.alias for f in spec.fields.values() if f.alias)
    candidates.extend(spec.groups.keys())
    candidates.extend(spec.presets.keys())

    matches = get_close_matches(name, sorted(set(candidates)), n=5, cutoff=0.4)
    if matches:
        console.print(f"Suggestions for '[bold]{name}[/bold]':")
        for m in matches:
            console.print(f"  {m}")
    else:
        console.print(f"No suggestions found for '{name}'.")
