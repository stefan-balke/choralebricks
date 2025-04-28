<h1 align="center">
<img src="https://raw.githubusercontent.com/stefan-balke/choralebricks/refs/heads/main/docs/img/logo_cb.png" width="300">
</h1><br>

[![CI](https://github.com/stefan-balke/choralebricks/actions/workflows/python-package.yml/badge.svg)](https://github.com/stefan-balke/choralebricks/actions/workflows/python-package.yml)

With this toolbox, we provide an easy way of accessing and interacting with the ChoraleBricks dataset.

For an overview of the dataset, please visit our demo website:<br />
[https://audiolabs-erlangen.de/resources/MIR/2025-ChoraleBricks](https://audiolabs-erlangen.de/resources/MIR/2025-ChoraleBricks)

If you use ChoraleBricks in your academic work, please cite this article:

:blue_book: Stefan Balke, Axel Berndt, and Meinard Müller
[**ChoraleBricks: A Modular Multitrack Dataset for Wind Music Research**](#)
Transactions of the International Society for Music Information Retrieval, 2025.


```bibtex
@article{BalkeBM24_ChoraleBricks,
  author  = {Stefan Balke and Axel Berndt and Meinard M{\"u}ller},
  title   = {{ChoraleBricks}: A Modular Multitrack Dataset for Wind Music Research},
  journal = {Transactions of the International Society for Music Information Retrieval},
  year    = {2025}
}
```

## :computer: Installation and Setup

Clone repository, then:

```bash
    pip install poetry
    poetry install
```

Dowload the corresponding audio files from Zenodo:

https://zenodo.org/records/15081741

## Usage

To use the full dataset, set a dataset `root_dir` directory

```python
cbdb = SongDB(root_dir="/path/to/ChoraleBricks")
```

where `root_dir` is the path to the ChoraleDB dataset folder.
The `root_dir` can also be overridden using a system environment variable.
Just ```export CHORALEDB_PATH=/path/to/ChoraleBricks``` inside your bash environment.
In that case no arguments would need to passed to `SongDB()`.

Further example scripts for different standard scenarios can be found in the `examples/` folder.

## Examples

As a starting point, we provide example code in the `examples/` folder.
These require slightly more dependencies. Use:
```bash
    poetry install --extras examples
```
for setup.

## Glossary

**song**

In this dataset, it groups all tracks of a certain chorale together.

**track**

A single track in a multi-track recording.

**voice**

Each chorale consists of 4 voices sometimes referred to sopran, alt, tenor, and bass (SATB).

**ensemble**

An ensemble is in the context of ChoraleBricks a set of four tracks (S, A, T, B).

## How to contribute

_ChoraleDB_ is a community focused project, we therefore encourage the community to submit bug-fixes and requests for technical support through [GitHub issues](https://github.com/stefan-balke/choralebricks/issues/new).

## License

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

## Acknowledgements

This work was funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under grant number 500643750 (MU 2686/15-1) and under Grant No. 555525568 (MU 2686/18-1).
The [International Audio Laboratories Erlangen](https://audiolabs-erlangen.de) are a joint institution of the [Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU)](https://www.fau.eu) and [Fraunhofer Institute for Integrated Circuits IIS](https://www.iis.fraunhofer.de/en.html).