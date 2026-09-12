#!/bin/bash

set -e

if [ "$#" -ne 2 ]; then
  echo "Invalid arguments."
  echo "Help: install-cli-commands <VENV_PATH> <SRC_PATH>"
  exit 1
fi

VENV_PATH="$1"
SRC_PATH=$(realpath $2)
COMMANDS=("tapen.py" "tpp.py")

echo "Installing local commands if needed"

venvAbsPath=$(realpath "$VENV_PATH")
commands_path=$(dirname $(realpath $0))

for c in "${COMMANDS[@]}"; do
  filename="${c%.*}"
  fullPath="$venvAbsPath/bin/$filename"
  if [[ -f "$fullPath" ]]; then
    printf "   %-15s: already exists\n" $filename
  else
    echo "#!$venvAbsPath/bin/python3" >$fullPath
    cat "$commands_path/${c}" | sed -e "s|\$SRC_DIR|$SRC_PATH|g" >>$fullPath
    chmod +x $fullPath
    printf "   %-15s: installed\n" $filename
  fi
done

echo "Local commands installed"
