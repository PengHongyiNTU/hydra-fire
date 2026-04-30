from __future__ import annotations

from .core.spec import ConfigSpec


def render_markdown_docs(spec: ConfigSpec) -> str:
    lines = [f"# {spec.app.name} CLI", ""]
    if spec.app.description:
        lines.extend([spec.app.description, ""])

    lines.extend(
        [
            "## Hydra",
            "",
            f"- Config path: `{spec.hydra.config_path}`",
            f"- Config name: `{spec.hydra.config_name}`",
            "",
        ]
    )
    lines.extend(_groups_section(spec))
    lines.extend(_fields_section(spec))
    lines.extend(_presets_section(spec))
    lines.extend(_raw_hydra_section())
    return "\n".join(lines).rstrip() + "\n"


def _groups_section(spec: ConfigSpec) -> list[str]:
    lines = ["## Groups", ""]
    if not spec.groups:
        return [*lines, "No groups configured.", ""]

    lines.extend(["| Name | Choices | Default | Help |", "|---|---|---|---|"])
    for name, group in spec.groups.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(name),
                    _cell(", ".join(group.choices)),
                    _cell(group.default or ""),
                    _cell(group.help),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _fields_section(spec: ConfigSpec) -> list[str]:
    lines = ["## Fields", ""]
    if not spec.fields:
        return [*lines, "No fields configured.", ""]

    lines.extend(
        [
            "| Name | Path | Alias | Type | Default | Visible | Help |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for name, field in spec.fields.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(name),
                    _cell(field.path),
                    _cell(field.alias or ""),
                    _cell(field.type),
                    _cell("" if field.default is None else str(field.default)),
                    _cell(str(field.visible).lower()),
                    _cell(field.help),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _presets_section(spec: ConfigSpec) -> list[str]:
    lines = ["## Presets", ""]
    if not spec.presets:
        return [*lines, "No presets configured.", ""]

    lines.extend(["| Name | Overrides | Description |", "|---|---|---|"])
    for name, preset in spec.presets.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(name),
                    _cell("<br>".join(f"`{override}`" for override in preset.overrides)),
                    _cell(preset.description),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def _raw_hydra_section() -> list[str]:
    return [
        "## Raw Hydra Overrides",
        "",
        "Raw Hydra syntax remains supported for advanced use:",
        "",
        "- `path.to.value=123` sets an existing value.",
        "- `+path.to.value=123` appends a new value.",
        "- `++path.to.value=123` sets or appends a value.",
        "- `~path.to.value` removes a value.",
        "",
        "Use `show` to preview the composed config and `run --dry-run` to inspect overrides.",
        "",
    ]


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()
