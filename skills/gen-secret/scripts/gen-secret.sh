#!/usr/bin/env bash
# gen-secret.sh — generate ONE random secret, then either print it or
# substitute it into a file in place. In file mode the secret is NEVER printed.
#
# The secret is only ever held in a shell variable: it never appears in
# argv (so it never shows up in `ps`), logs, or stdout in file mode.
set -euo pipefail

length=32
charset=alnum
no_ambiguous=false
prefix=""
file=""
key=""
placeholder=""
append=false
backup=true
quiet=false

usage() {
  cat >&2 <<'EOF'
usage: gen-secret.sh [generation options] [target options]

generation:
  -l, --length N        secret length in characters (default: 32)
  -c, --charset NAME    hex | digit | alpha | alnum | urlsafe | base64 | full
                        hex:     0-9a-f              (dotenv-safe)
                        digit:   0-9                 (dotenv-safe)
                        alpha:   A-Za-z              (dotenv-safe)
                        alnum:   A-Za-z0-9           (default, dotenv-safe)
                        urlsafe: A-Za-z0-9_-         (dotenv+URL safe)
                        base64:  A-Za-z0-9+/         (needs quotes in dotenv)
                        full:    alnum + !#$%&()*+,./:;<=>?@^_{|}~-
                                                       (needs quotes in dotenv)
      --no-ambiguous    also exclude 0 O 1 l I
      --prefix STR      prepend a literal prefix (not counted in --length)

target (default: print the secret to stdout):
  -f, --file PATH       edit PATH in place; requires exactly one of -k / -p.
                        The secret is NOT printed in this mode.
  -k, --key KEY         replace the value of every `KEY=...` line
                        (also matches `export KEY=`); trailing inline
                        comments on those lines are dropped
      --append          with -k: append `KEY=<secret>` if KEY is absent;
                        creates PATH (mode 600) if it does not exist
  -p, --placeholder STR replace every literal occurrence of STR in PATH
                        (all occurrences get the SAME secret)
      --no-backup       skip the default PATH.bak.<timestamp> backup
  -q, --quiet           no confirmation output in file mode
EOF
}

die() { echo "gen-secret: error: $*" >&2; exit 1; }

[[ $# -gt 0 ]] || { usage; exit 2; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -l|--length)       length="${2:?missing value for $1}"; shift 2 ;;
    -c|--charset)      charset="${2:?missing value for $1}"; shift 2 ;;
    --no-ambiguous)    no_ambiguous=true; shift ;;
    --prefix)          prefix="${2:?missing value for $1}"; shift 2 ;;
    -f|--file)         file="${2:?missing value for $1}"; shift 2 ;;
    -k|--key)          key="${2:?missing value for $1}"; shift 2 ;;
    --append)          append=true; shift ;;
    -p|--placeholder)  placeholder="${2:?missing value for $1}"; shift 2 ;;
    --no-backup)       backup=false; shift ;;
    -q|--quiet)        quiet=true; shift ;;
    -h|--help)         usage; exit 0 ;;
    *)                 die "unknown option: $1 (see --help)" ;;
  esac
done

[[ "$length" =~ ^[1-9][0-9]*$ ]] || die "--length must be a positive integer, got: $length"

case "$charset" in
  hex)     chars='0-9a-f' ;;
  digit)   chars='0-9' ;;
  alpha)   chars='A-Za-z' ;;
  alnum)   chars='A-Za-z0-9' ;;
  urlsafe) chars='A-Za-z0-9_-' ;;
  base64)  chars='A-Za-z0-9+/' ;;
  full)    chars='A-Za-z0-9!#$%&()*+,./:;<=>?@^_{|}~-' ;;
  *)       die "unknown charset: $charset (hex|digit|alpha|alnum|urlsafe|base64|full)" ;;
esac

if [[ -n "$file" ]]; then
  { [[ -n "$key" ]] && [[ -n "$placeholder" ]]; } && die "use only one of --key / --placeholder"
  { [[ -z "$key" ]] && [[ -z "$placeholder" ]]; } && die "--file requires --key or --placeholder"
else
  $append && die "--append requires --file --key"
fi
if [[ -n "$key" ]]; then
  [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || die "invalid key name: $key"
fi

# --- generate ---------------------------------------------------------------
drop=''
$no_ambiguous && drop='0O1lI'

secret="$(
  set +o pipefail  # tr exits on SIGPIPE once head has enough bytes
  if [[ -n "$drop" ]]; then
    LC_ALL=C tr -dc "$chars" < /dev/urandom | LC_ALL=C tr -d "$drop" | head -c "$length"
  else
    LC_ALL=C tr -dc "$chars" < /dev/urandom | head -c "$length"
  fi
)"
[[ ${#secret} -eq $length ]] || die "generation failed (got ${#secret} chars, wanted $length)"
secret="${prefix}${secret}"

# --- stdout mode -------------------------------------------------------------
if [[ -z "$file" ]]; then
  printf '%s\n' "$secret"
  exit 0
fi

# --- file mode ---------------------------------------------------------------
say() { $quiet || printf '%s\n' "$*"; }

if [[ ! -f "$file" ]]; then
  if $append && [[ -n "$key" ]]; then
    ( umask 077; printf '%s=%s\n' "$key" "$secret" > "$file" )
    say "OK: created $file with $key=<secret> (mode 600, secret not shown)"
    exit 0
  fi
  die "file not found: $file"
fi

bak=''
if $backup; then
  bak="${file}.bak.$(date +%Y%m%d%H%M%S)"
  cp -p -- "$file" "$bak"
fi

if [[ -n "$placeholder" ]]; then
  # bash pattern substitution with a quoted pattern matches literally —
  # no regex-escaping pitfalls, no external tools
  content="$(cat -- "$file"; printf x)"; content="${content%x}"
  [[ "$content" == *"$placeholder"* ]] || die "placeholder not found in $file: $placeholder"
  stripped="${content//"$placeholder"/}"
  count=$(( (${#content} - ${#stripped}) / ${#placeholder} ))
  printf '%s' "${content//"$placeholder"/"$secret"}" > "$file"
  say "OK: replaced $count occurrence(s) of placeholder in $file${bak:+ (backup: $bak)}; secret not shown"
  exit 0
fi

# key mode
replaced=0
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
while IFS= read -r line || [[ -n "$line" ]]; do
  case "$line" in
    "$key="*)
      printf '%s=%s\n' "$key" "$secret" >> "$tmp"; replaced=$((replaced+1)) ;;
    "export $key="*)
      printf 'export %s=%s\n' "$key" "$secret" >> "$tmp"; replaced=$((replaced+1)) ;;
    *)
      printf '%s\n' "$line" >> "$tmp" ;;
  esac
done < "$file"

if [[ $replaced -eq 0 ]]; then
  if $append; then
    printf '%s=%s\n' "$key" "$secret" >> "$tmp"
    cat -- "$tmp" > "$file"   # keep original inode/permissions
    say "OK: appended $key=<secret> to $file${bak:+ (backup: $bak)}; secret not shown"
    exit 0
  fi
  die "key not found in $file: $key (use --append to add it)"
fi

cat -- "$tmp" > "$file"
say "OK: replaced $replaced occurrence(s) of $key in $file${bak:+ (backup: $bak)}; secret not shown"
