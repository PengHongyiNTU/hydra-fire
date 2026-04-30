from hydra_fire.core.spec import ArgumentField, ConfigGroup, ConfigSpec, HydraConfig, Preset
from hydra_fire.docs import render_markdown_docs


def test_render_markdown_docs_includes_groups_fields_presets_and_raw_hydra_help():
    spec = ConfigSpec(
        hydra=HydraConfig(config_path="configs", config_name="config"),
        fields={
            "size": ArgumentField(
                path="job.size",
                alias="size",
                type="int",
                default=10,
                help="Work item size.",
            )
        },
        groups={"job": ConfigGroup(name="job", choices=["baseline"], default="baseline")},
        presets={
            "quick": Preset(
                overrides=["job=baseline", "job.size=1"],
                description="Quick run.",
            )
        },
    )

    markdown = render_markdown_docs(spec)

    assert "# hydra-fire CLI" in markdown
    assert "| job | baseline | baseline |" in markdown
    assert "| size | job.size | size | int | 10 | true | Work item size. |" in markdown
    assert "`job=baseline`<br>`job.size=1`" in markdown
    assert "++path.to.value=123" in markdown


def test_cli_config_reference_documents_generated_file_contract():
    reference = open("docs/CLI_CONFIG.md").read()

    assert "# CLI Config Reference" in reference
    assert "## Complete Example" in reference
    assert "trainer.batch_size" in reference
    assert "groups:" in reference
    assert "presets:" in reference
    assert "Source Mapping" in reference
