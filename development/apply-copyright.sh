#!/usr/bin/env bash

if [ -z "${NO_VENV}" ]; then source venv/bin/activate; fi;

if [ "$#" -eq "0" ]; then
  echo "No changed files";
  exit 0;
fi

licenseheaders -t ./development/copyright.tmpl -E ".py" -cy -f "$@";
