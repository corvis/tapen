#!/usr/bin/env bash

if [ "$#" -eq "0" ]; then
  echo "No changed files";
  exit 0;
fi

uv run licenseheaders -t ./development/copyright.tmpl -E ".py" -cy -f "$@";
