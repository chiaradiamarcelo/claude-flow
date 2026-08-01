#!/usr/bin/env bash
# Run the three quality oracles against a golden-repo-spring copy and print a summary.
#   Usage: run-oracle.sh <arm-repo-dir>
#
# Split design (Spring Boot 4 forces JUnit 6, which PIT cannot drive):
#   - green build + JaCoCo (CRAP) + detekt (DRY)  ... run in the arm repo (JUnit 6).
#   - mutation (PIT)                              ... run in a pure-Kotlin sidecar built
#     from the arm's framework-free domain + application sources and their unit tests
#     (the tests that do NOT import Spring), on JUnit 5. See oracle/pit-sidecar/.
set -uo pipefail
REPO="${1:?usage: run-oracle.sh <arm-repo-dir>}"
REPO="$(cd "$REPO" && pwd)"
HERE="$(cd "$(dirname "$0")" && pwd)"
SIDECAR_TPL="$HERE/pit-sidecar"

echo "### [1/3] arm build: test + jacoco + cpd (JUnit 6)"
( cd "$REPO" && ./gradlew clean test jacocoTestReport cpdCheck --no-daemon -q 2>&1 | tail -4 )

echo "### [2/3] mutation sidecar (JUnit 5 + PIT)"
SC="$REPO/build/pit-sidecar"
rm -rf "$SC"; mkdir -p "$SC/src/main/kotlin" "$SC/src/test/kotlin"
cp "$SIDECAR_TPL/build.gradle.kts" "$SIDECAR_TPL/settings.gradle.kts" \
   "$SIDECAR_TPL/gradle.properties" "$SIDECAR_TPL/gradlew" "$SIDECAR_TPL/gradlew.bat" "$SC/"
cp -R "$SIDECAR_TPL/gradle" "$SC/gradle"
# framework-free production: domain + application packages
for pkg in domain application; do
  find "$REPO/src/main/kotlin" -type d -name "$pkg" | while read -r d; do
    rel="${d#"$REPO"/src/main/kotlin/}"; mkdir -p "$SC/src/main/kotlin/$(dirname "$rel")"
    cp -R "$d" "$SC/src/main/kotlin/$(dirname "$rel")/"
  done
done
# unit tests that don't touch Spring (grep -L = files NOT matching)
find "$REPO/src/test/kotlin" -name "*.kt" -print0 \
  | xargs -0 grep -L -e "org.springframework" -e "@DataJpaTest" -e "@WebMvcTest" -e "@SpringBootTest" 2>/dev/null \
  | while read -r f; do
      rel="${f#"$REPO"/src/test/kotlin/}"; mkdir -p "$SC/src/test/kotlin/$(dirname "$rel")"
      cp "$f" "$SC/src/test/kotlin/$rel"
    done
( cd "$SC" && ./gradlew test pitest --no-daemon -q 2>&1 | tail -4 )

echo
echo "======== ORACLE SUMMARY: $REPO ========"
python3 - "$SC/build/reports/pitest/mutations.xml" \
           "$REPO/build/reports/jacoco/test/jacocoTestReport.xml" \
           "$REPO/build/reports/cpd/cpdCheck.xml" "$HERE/crap.py" <<'PY'
import sys, os, xml.etree.ElementTree as ET, importlib.util
mut, jac, det, crap_py = sys.argv[1:5]
if os.path.exists(mut):
    ms = ET.parse(mut).getroot().findall('mutation')
    killed = [m for m in ms if m.get('status') == 'KILLED']
    print(f"mutation:  {len(killed)}/{len(ms)} killed  ({100*len(killed)/len(ms) if ms else 0:.0f}%)")
else:
    print("mutation:  (no report)")
if os.path.exists(jac):
    spec = importlib.util.spec_from_file_location("crap", crap_py)
    crap = importlib.util.module_from_spec(spec); spec.loader.exec_module(crap)
    r = crap.analyse(jac)
    print(f"crap:      methods={r['methods']}  over30={r['over_threshold']}  total={r['total_crap']}  mean={r['mean_crap']}")
else:
    print("crap:      (no jacoco report)")
if os.path.exists(det):
    dups = ET.parse(det).getroot().findall('duplication')
    dup_lines = sum(int(d.get('lines', 0)) for d in dups)
    print(f"cpd/DRY:   {len(dups)} duplication blocks, {dup_lines} duplicated lines")
else:
    print("cpd/DRY:   (no report)")
PY
