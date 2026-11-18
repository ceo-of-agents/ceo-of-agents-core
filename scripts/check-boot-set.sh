#!/bin/sh
# Measure an hq's boot set against byte budgets and check the pending lines.
#
# Usage: sh check-boot-set.sh [hq-dir]      (default: the current directory)
#
# Prints the size of each boot file against its budget, the lines of
# company/state.md longer than 300 characters, and the lines of the section
# "Waiting on the CEO" that do not follow the line format of schemas/state.md,
# and, only when the optional company/todo.md exists (not part of the boot
# set), its item lines that do not follow schemas/todo.md. The last line is "verdict: ok" or "verdict: N issue(s)". Changes nothing on
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
      return out
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

# The CEO todo list is optional and outside the boot set: no size budget, and
# nothing is printed when it is missing, so an hq without it reads as before.
todo="$dir/company/todo.md"
if [ -f "$todo" ]; then
  report=$(LC_ALL=C awk '
    function first8(s,   n, a, i, out) {
      n = split(s, a, /[ \t]+/); out = ""
      for (i = 1; i <= n && i <= 8; i++) if (a[i] != "") out = out (out == "" ? "" : " ") a[i]
      return out
    }
    BEGIN { item = "^- [A-Za-z0-9]+-T[0-9]+ \\[(high|normal|low)\\]: [^ ].* \\(" }
    {
      sub(/\r$/, "")
      if ($0 ~ /^## /) {
        sect = ($0 == "## Open") ? "open" : ($0 == "## Done (last 7 days)") ? "done" : ""
        next
      }
      if (sect == "" || $0 !~ /^- / || $0 == "- none") next
      date = "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]\\)$"
      if (sect == "open" && $0 ~ (item "since " date)) next
      if (sect == "done" && $0 ~ (item "done " date)) next
      n++
      if (n <= 3) print "Q   line " NR ": " first8($0)
    }
    END {
      if (n > 3) print "Q   and " (n - 3) " more"
      print "T " (n + 0)
    }' "$todo")
  extra=$(printf '%s\n' "$report" | sed -n 's/^T //p')
  issues=$((issues + extra))
  echo "company/todo.md lines not in the line format: $extra"
  printf '%s\n' "$report" | sed -n 's/^Q //p'
fi

if [ "$issues" -eq 0 ]; then
  echo "verdict: ok"
else
  echo "verdict: $issues issue(s)"
fi
exit 0
