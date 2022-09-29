
![Tapen Picture](https://raw.githubusercontent.com/corvis/tapen/master/docs/assets/cover-picture.png "Tapen cover image")


<h2 align="center">Tapen</h2>

<p align="center">
  <a href="https://pypi.org/project/tapen/"><img src="https://img.shields.io/pypi/l/tapen?style=for-the-badge" title="License: GPLv3"/></a> 
  <a href="https://pypi.org/project/tapen/"><img src="https://img.shields.io/pypi/pyversions/tapen?style=for-the-badge" title="Python Versions"/></a> 
  <a href="https://github.com/psf/black/"><img src="https://img.shields.io/badge/Code%20Style-black-black?style=for-the-badge" title="Code style: black"/></a> 
  <a href="https://pypi.org/project/tapen/"><img src="https://img.shields.io/pypi/v/tapen?style=for-the-badge" title="PyPy Version"/></a> 
  <a href="https://pypi.org/project/tapen/"><img src="https://img.shields.io/pypi/dm/tapen?style=for-the-badge" title="PyPy Downloads"/></a> 
  <br>
  <a href="https://github.com/corvis/tapen/actions?query=workflow%3A%22Sanity+Check"><img src="https://img.shields.io/github/workflow/status/corvis/tapen/Sanity%20Check?style=for-the-badge" title="Build Status"/></a> 
  <a href="https://app.codacy.com/gh/corvis/tapen/dashboard"><img src="https://img.shields.io/codacy/grade/7aa38cc5c1b14aa9ab06ee8af45d5cff?style=for-the-badge&_nocahe=1" title="Codacy Grade"/></a> 
  <a href="https://github.com/corvis/tapen/"><img src="https://img.shields.io/github/last-commit/corvis/tapen?style=for-the-badge" title="Last Commit"/></a> 
  <a href="https://github.com/corvis/tapen/releases/"><img src="https://img.shields.io/github/release-date/corvis/tapen?style=for-the-badge" title="Last Release"/></a> 
</p>


**Tapen** is a tool for composing and printing labels on label printers. At the moment only Brother printers are supported.
Developed and tested on linux only.


## Basic Usage

Just print a line of text covering all available height of the tape:

```shell
tapen print "Hello world"
```

Shortcut version: `tpp "Hello world"`.

**Note**: Short syntax (`tpp ...` command is equal to `tapen print ...`). Here and bellow in the docs we will use short
syntax for simplicity.

Print multiple labels at time:

```shell
tpp "Label 1" "label 2" "Label 3"
```

Print 2 copies of of each label:

```shell
tpp -q 2 "Label 1" "Label 2"
```

## Installation

There are a couple of possible installation methods:

1. With pip: `pip install tapen`
2. Use pre-compiled binary. Just download binary from [releases page](https://github.com/corvis/tapen/releases)

# Credits

* Dmitry Berezovsky (@corvis) - author and main maintainer
* Dominic Radermacher (blip@mockmoon-cybernetics.ch) - creator of libptouch, the source code of this library was used to understand the interface to Brotehr devices.
* [CLI Rack](https://github.com/corvis/cli-rack)

# Disclaimer

This module is licensed under MIT. This means you are free to use it in commercial projects.

The GPLv3 license clearly explains that there is no warranty for this free software. Please see the included LICENSE file
for details.
