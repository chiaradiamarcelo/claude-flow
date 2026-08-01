#!/usr/bin/env python3
"""Merge the JaCoCo + CPD oracle config into an arm's (developer-modified) build.gradle.kts.

Non-destructive: inserts the two plugins after the spring dependency-management plugin
line and appends the jacoco/cpd configuration + the pmd-kotlin cpd dependency. Leaves the
developer's own changes (extra test modules, Flyway, etc.) intact.

Usage: apply-oracle-build.py <arm-repo-dir>
"""
import sys, pathlib

ORACLE_BLOCK = '''

// ==== Experiment oracle (added post-hoc; not present during the developer run) ====
jacoco { toolVersion = "0.8.12" }
tasks.named<JacocoReport>("jacocoTestReport") {
    dependsOn(tasks.named("test"))
    reports { xml.required.set(true); html.required.set(true) }
}
tasks.named("test") { finalizedBy(tasks.named("jacocoTestReport")) }

cpd {
    language = "kotlin"
    minimumTokenCount = 50
    isIgnoreFailures = true
    toolVersion = "7.7.0"
}
dependencies { "cpd"("net.sourceforge.pmd:pmd-kotlin:7.7.0") }
tasks.named<de.aaschmid.gradle.plugins.cpd.Cpd>("cpdCheck") {
    reports { xml.required.set(true); text.required.set(false) }
    source = files("src/main/kotlin").asFileTree
}
'''


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    bg = pathlib.Path(argv[1]) / "build.gradle.kts"
    text = bg.read_text()
    if "Experiment oracle (added post-hoc" in text:
        print("already applied"); return 0
    lines = text.splitlines()
    out, inserted = [], False
    for ln in lines:
        out.append(ln)
        if not inserted and "io.spring.dependency-management" in ln:
            out.append('    jacoco')
            out.append('    id("de.aaschmid.cpd") version "3.5"')
            inserted = True
    if not inserted:
        print("ERROR: could not find dependency-management plugin anchor"); return 1
    bg.write_text("\n".join(out) + ORACLE_BLOCK)
    print(f"oracle build applied to {bg}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
