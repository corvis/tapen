#!/bin/bash

DEPS=("python3.14" "poetry" "sed")

COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_NC='\033[0m' # No Color

echo "Verifying required dependencies"
echo ""

for d in "${DEPS[@]}"; do
  if [ -n "$(which "$d")" ]; then
    printf "   %-25s: installed\n" $d
  else
    printf "   %-25s: %b\n" $d "${COLOR_RED}NOT INSTALLED${COLOR_NC}"
    if [ "$d" == "poetry" ]; then
      echo ""
      printf "${COLOR_YELLOW}Please install poetry on a system level. In order to install poetry you could run the following command:${COLOR_NC}"
      echo ""
      echo "curl -sSL https://install.python-poetry.org | python3 -"
      echo ""
      echo "${COLOR_YELLOW}It is also recommended to install python packages ${COLOR_RED}keyring${COLOR_YELLOW} and ${COLOR_RED}artifacts-keyring${COLOR_NC}"
      echo ""
      echo "pip install keyring artifacts-keyring"
      echo ""
    fi
    exit 1
  fi
done

echo ""
echo "All dependencies installed"
