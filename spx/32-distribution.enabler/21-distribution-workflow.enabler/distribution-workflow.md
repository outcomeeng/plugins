# Distribution Workflow

PROVIDES the repository workflow that runs downstream skill distribution against built marketplace artifacts
SO THAT marketplace maintainers and continuous integration
CAN publish downstream skill repositories from the same declared project environment

## Assertions

### Compliance

- ALWAYS: preserve the target repository's `.git/` directory when clearing its distribution contents ([audit])
- ALWAYS: the distribution workflow triggers from the committed Claude runtime tree and source plugin changes — retired `plugins/` source paths never gate distribution ([test](tests/test_distribution_workflow.compliance.l1.py))
- ALWAYS: the distribution workflow runs on the Python version declared by `pyproject.toml` — CI uses the same interpreter contract as the project metadata ([test](tests/test_distribution_workflow.compliance.l1.py))
