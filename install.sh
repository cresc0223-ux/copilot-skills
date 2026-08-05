#!/usr/bin/env sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source_dir="$repo_dir/skills/local-short-video"
destination=""
install_dependencies=0

for argument in "$@"; do
  case "$argument" in
    --install-dependencies)
      install_dependencies=1
      ;;
    *)
      if [ -n "$destination" ]; then
        echo "Only one destination path is supported." >&2
        exit 2
      fi
      destination=$argument
      ;;
  esac
done

if [ ! -f "$source_dir/SKILL.md" ]; then
  echo "Skill source is incomplete: $source_dir" >&2
  exit 2
fi

if [ -z "$destination" ]; then
  codex_root=${CODEX_HOME:-"$HOME/.codex"}
  destination="$codex_root/skills/local-short-video"
fi

parent_dir=$(dirname -- "$destination")
mkdir -p "$parent_dir"

backup=""
if [ -e "$destination" ]; then
  backup="$destination.backup-$(date +%Y%m%d-%H%M%S)"
  mv "$destination" "$backup"
fi

if ! cp -R "$source_dir" "$destination"; then
  if [ -n "$backup" ] && [ ! -e "$destination" ]; then
    mv "$backup" "$destination"
  fi
  exit 1
fi

if [ "$install_dependencies" -eq 1 ]; then
  python_command=${PYTHON:-python3}
  "$python_command" -m pip install -r "$repo_dir/requirements.txt"
fi

echo "Installed local-short-video to: $destination"
if [ -n "$backup" ]; then
  echo "Previous installation backed up to: $backup"
fi
echo 'Reload Codex, then invoke $local-short-video.'
