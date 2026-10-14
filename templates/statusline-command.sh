#!/usr/bin/env bash

input=$(cat)

used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
model=$(echo "$input" | jq -r '.model.display_name // empty')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')

# Shorten cwd: replace $HOME with ~
home="$HOME"
cwd="${cwd/#$home/\~}"

BAR_WIDTH=20

if [ -n "$used" ] && [ "$used" != "null" ]; then
  used_int=$(printf "%.0f" "$used")
  filled=$(( used_int * BAR_WIDTH / 100 ))
  empty=$(( BAR_WIDTH - filled ))

  bar=""
  for ((i=0; i<filled; i++)); do bar="${bar}█"; done
  for ((i=0; i<empty; i++)); do bar="${bar}░"; done

  # Color: green < 50%, yellow 50-80%, red > 80%
  if [ "$used_int" -lt 50 ]; then
    color="\033[32m"   # green
  elif [ "$used_int" -lt 80 ]; then
    color="\033[33m"   # yellow
  else
    color="\033[31m"   # red
  fi
  reset="\033[0m"

  printf "${color}[${bar}]${reset} %d%% used | %s | %s" "$used_int" "$model" "$cwd"
else
  printf "%s | %s" "$model" "$cwd"
fi
