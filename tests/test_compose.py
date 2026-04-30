from hydra_fire.compose import compose_config


def test_compose_config_with_expanded_override():
    cfg = compose_config(
        config_path="tests/fixtures/configs",
        config_name="config",
        overrides=["job=baseline", "job.size=16"],
    )

    assert cfg.job.size == 16
    assert cfg.job.name == "baseline"
