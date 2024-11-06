# ChoraleBricks

[![Python package](https://github.com/stefan-balke/choralebricks/actions/workflows/python-package.yml/badge.svg)](https://github.com/stefan-balke/choralebricks/actions/workflows/python-package.yml)

WIP

## Installation and Setup

Clone repository, then:

```
    pip install poetry
    poetry install
```

Dowload the corresponding audio files from Zenodo: TODO.

## Usage

To use the full dataset, set a dataset `root_dir` directory 

```python
cbdb = SongDB(root_dir="/path/to/ChoraleBricks")
```

where `root_dir` is the path to the ChoraleDB dataset folder.
The `root_dir` can also be overridden using a system environment variable.
Just ```export CHORALEDBPATH=/path/to/ChoraleBricks``` inside your bash environment.
In that case no arguments would need to passed to `SongDB()`.

Further example scripts for different standard scenarios can be found in the `examples/` folder.

## Glossary

**song**

In this dataset, it groups all tracks of a certain chorale together.

**track**

A single track in a multi-track recording.

**voice**

Each chorale consists of 4 voices sometimes referred to sopran, alt, tenor, and bass (SATB).

## Cite

```latex
@article(TODO)
```

## How to contribute

_ChoraleDB_ is a community focused project, we therefore encourage the community to submit bug-fixes and requests for technical support through [github issues](https://github.com/stefan-balke/choralebricks/issues/new).

## License

MIT