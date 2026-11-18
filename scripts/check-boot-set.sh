#!/bin/sh
# Measure an hq's boot set against byte budgets and check the pending lines.
#
# Usage: sh check-boot-set.sh [hq-dir]      (default: the current directory)
#
# Prints the size of each boot file against its budget, the lines of
# company/state.md longer than 300 characters, and the lines of the section
# "Waiting on the CEO" that do not follow the line format of schemas/state.md.
# The last line is "verdict: ok" or "verdict: N issue(s)". Changes nothing on
# disk and exits 0, except exit 2 when the argument is not a directory.
#
# The budgets below must match the table in schemas/boot-set.md; the CI check
# scripts/ci/check_boot_set.py keeps them in sync.

# BUDGETS BEGIN
BUDGETS='CLAUDE.md 24576
org.yaml 6144
company/vision.md 4096
company/strategy.md 4096
company/state.md 8192
company/decision-queue.md 10240
accounts.local.yaml 2048
TOTAL 40960'
# BUDGETS END

# Budget of one initiative page, initiatives/<slug>/status.md. Pages are not in
# the boot set, but drift the same way, so their size and their lines over 300
# characters are reported too ("Initiative pages" in schemas/boot-set.md; the CI
# check keeps this number in sync).
STATUS_BUDGET=4096

dir=${1:-.}
if [ ! -d "$dir" ]; then
  echo "usage: sh check-boot-set.sh [hq-dir]" >&2
  echo "error: not a directory: $dir" >&2
  exit 2
fi

echo "boot set of $dir (budgets in bytes; 1 KiB = 1024 bytes)"

issues=0
total=0
total_budget=0

# Per-file sizes. Here-doc (not a pipe) so the counters stay in this shell.
while read -r name budget; do
  if [ "$name" = "TOTAL" ]; then
    total_budget=$budget
    continue
  fi
  if [ -f "$dir/$name" ]; then
    size=$(wc -c < "$dir/$name" | tr -d ' \t\n')
    shown="$size bytes"
  else
    size=0
    shown="missing, counted as 0 bytes"
  fi
  total=$((total + size))
  if [ "$size" -gt "$budget" ]; then
    verdict="over by $((size - budget)) bytes"
    issues=$((issues + 1))
  else
    verdict=ok
  fi
  echo "$name: $shown, budget $budget: $verdict"
done <<EOF
$BUDGETS
EOF

if [ "$total" -gt "$total_budget" ]; then
  verdict="over by $((total - total_budget)) bytes"
  issues=$((issues + 1))
else
  verdict=ok
fi
echo "whole boot set: $total bytes, budget $total_budget: $verdict"

# Initiative pages: printed only when at least one exists, so an hq without
# initiatives reads as before. Paths are shown relative to the hq.
npages=0
big=0
long=0
quotes=""
for page in "$dir"/initiatives/*/status.md; do
  [ -f "$page" ] || continue
  npages=$((npages + 1))
  name=${page#"$dir"/}
  size=$(wc -c < "$page" | tr -d ' \t\n')
  if [ "$size" -gt "$STATUS_BUDGET" ]; then
    big=$((big + 1))
    quotes="$quotes
B   $name: $size bytes, over by $((size - STATUS_BUDGET)) bytes"
  fi
  # Characters, not bytes: the same count as for company/state.md below.
  found=$(LC_ALL=C awk -v name="$name" '
    function chars(s,   t) { t = s; gsub(/[\200-\277]/, "", t); return length(t) }
    function first8(s,   n, a, i, out) {
      n = split(s, a, /[ \t]+/); out = ""
      for (i = 1; i <= n && i <= 8; i++) if (a[i] != "") out = out (out == "" ? "" : " ") a[i]
      return cut(out)
    }
    # At most 80 characters; never splits a UTF-8 character.
    function cut(s,   i, n, b) {
      n = 0
      for (i = 1; i <= length(s); i++) {
        b = substr(s, i, 1)
        if (b !~ /[\200-\277]/ && ++n > 77) return substr(s, 1, i - 1) "..."
      }
      return s
    }
    { sub(/\r$/, ""); c = chars($0); if (c > 300) print "L   " name " line " NR " (" c " characters): " first8($0) }' "$page")
  if [ -n "$found" ]; then
    long=$((long + $(printf '%s\n' "$found" | wc -l | tr -d ' \t\n')))
    quotes="$quotes
$found"
  fi
done
if [ "$npages" -gt 0 ]; then
  issues=$((issues + big + long))
  echo "initiative pages over $STATUS_BUDGET bytes: $big"
  printf '%s\n' "$quotes" | sed -n 's/^B //p' | sed -n '1,3p'
  [ "$big" -gt 3 ] && echo "  and $((big - 3)) more"
  echo "initiative page lines over 300 characters: $long"
  printf '%s\n' "$quotes" | sed -n 's/^L //p' | sed -n '1,3p'
  [ "$long" -gt 3 ] && echo "  and $((long - 3)) more"
fi

state="$dir/company/state.md"
if [ ! -f "$state" ]; then
  echo "company/state.md missing: line and pending checks skipped"
else
  # Both reports come from one awk program, run in the C locale so that
  # length() counts bytes; characters are counted by first deleting the UTF-8
  # continuation bytes (octal 200-277), which leaves one byte per character.
  # Output lines: "N <count>" per group, then "Q <group> <text>" per quoted line.
  report=$(LC_ALL=C awk '
    function chars(s,   t) { t = s; gsub(/[\200-\277]/, "", t); return length(t) }
    function first8(s,   n, a, i, out) {
      n = split(s, a, /[ \t]+/); out = ""
      for (i = 1; i <= n && i <= 8; i++) if (a[i] != "") out = out (out == "" ? "" : " ") a[i]
      return cut(out)
    }
    # At most 80 characters; never splits a UTF-8 character.
    function cut(s,   i, n, b) {
      n = 0
      for (i = 1; i <= length(s); i++) {
        b = substr(s, i, 1)
        if (b !~ /[\200-\277]/ && ++n > 77) return substr(s, 1, i - 1) "..."
      }
      return s
    }
    function add(g, text) {
      count[g]++
      if (count[g] <= 3) quote[g, count[g]] = text
    }
    {
      sub(/\r$/, "")
      c = chars($0)
      if (c > 300) add("long", "line " NR " (" c " characters): " first8($0))
      if ($0 ~ /^## /) inpend = ($0 == "## Waiting on the CEO")
      else if (inpend && $0 ~ /^- / && $0 != "- none") {
        if ($0 ~ /^- [A-Za-z0-9]+-[AD][0-9]+ \[(high|normal|low)\] \{(ok|do|decide)\}: ./) {
          if ($0 ~ /^- [A-Za-z0-9]+-A[0-9]+ \[[a-z]+\] \{decide\}/ || \
              $0 ~ /^- [A-Za-z0-9]+-D[0-9]+ \[[a-z]+\] \{(ok|do)\}/)
            add("fit", "line " NR ": " first8($0))
        } else if ($0 ~ /^- [A-Za-z0-9]+-[AD][0-9]+ \[(high|normal|low)\]: /)
          add("nokind", "line " NR ": " first8($0))
        else add("bad", "line " NR ": " first8($0))
      }
    }
    function show(g, title,   i, n) {
      n = count[g] + 0
      print "N " title ": " n
      for (i = 1; i <= n && i <= 3; i++) print "Q   " quote[g, i]
      if (n > 3) print "Q   and " (n - 3) " more"
    }
    END {
      show("long", "company/state.md lines over 300 characters")
      show("nokind", "pending lines without a kind")
      show("fit", "pending lines whose kind does not fit the code")
      show("bad", "pending lines not in the line format")
      print "T " (count["long"] + count["nokind"] + count["fit"] + count["bad"])
    }' "$state")
  extra=$(printf '%s\n' "$report" | sed -n 's/^T //p')
  issues=$((issues + extra))
  printf '%s\n' "$report" | sed -n -e 's/^N //p' -e 's/^Q //p'
fi

if [ "$issues" -eq 0 ]; then
  echo "verdict: ok"
else
  echo "verdict: $issues issue(s)"
fi
exit 0
