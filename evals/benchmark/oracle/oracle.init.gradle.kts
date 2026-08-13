// Applies the measurement oracle to a project WITHOUT editing its build files.
//
// Used as: ./gradlew --init-script ../oracle/oracle.init.gradle.kts <tasks>
//
// Why an init script and not the fixture's build.gradle.kts: the pipeline's agents
// read the build file. An agent that can see it is being mutation-scored can, in
// principle, write to the score rather than to the specification. Keeping the
// oracle out-of-band keeps every arm blind.
//
// Toolchain traps this encodes, carried from finding 14 via mutation-audit.md:
//   - gradle-pitest-plugin >= 1.19 is required for Gradle 9 (1.15.0, the latest on
//     Maven Central, dies on ReportingExtension.baseDir which Gradle 9 removed).
//     1.19.0 is published to the GRADLE PLUGIN PORTAL, not Maven Central — the
//     initscript repositories below must include gradlePluginPortal() or the
//     resolution silently falls back to the too-old Central copy.
//   - PIT's forked JVM must be a plain Temurin JDK (Android Studio's JBR crashes
//     the coverage minion with "Minion exited abnormally / UNKNOWN_ERROR")
//   - target classes must be Java-21 bytecode or PIT's bundled ASM cannot read
//     them; the fixture's build sets jvmTarget accordingly
initscript {
    repositories { gradlePluginPortal(); mavenCentral() }
    dependencies {
        classpath("info.solidsoft.gradle.pitest:gradle-pitest-plugin:1.19.0")
    }
}

allprojects {
    afterEvaluate {
        if (plugins.hasPlugin("java")) {
            apply(plugin = "jacoco")  // core plugin: id is fine
            apply<info.solidsoft.gradle.pitest.PitestPlugin>()

            extensions.configure<JacocoPluginExtension>("jacoco") {
                toolVersion = "0.8.12"
            }

            tasks.named("jacocoTestReport") {
                dependsOn(tasks.named("test"))
                (this as org.gradle.testing.jacoco.tasks.JacocoReport).reports {
                    xml.required.set(true)   // crap.py consumes the XML
                    html.required.set(false)
                }
            }

            extensions.configure<info.solidsoft.gradle.pitest.PitestPluginExtension>("pitest") {
                pitestVersion.set("1.19.1")
                junit5PluginVersion.set("1.2.2")
                // Framework-free business logic only. Mutating controllers and JPA
                // adapters is slow and low-value (finding 14) and would flood the
                // survivor list with wiring noise.
                targetClasses.set(listOf("com.example.bank.domain.*", "com.example.bank.application.*"))
                outputFormats.set(listOf("XML"))
                timestampedReports.set(false)
                threads.set(4)
                failWhenNoMutations.set(false)
                // The plugin otherwise injects its own junit-platform-launcher into
                // testRuntimeOnly, which misaligns with the engine Boot manages and
                // makes Jupiter fail discovery with "OutputDirectoryProvider not
                // available". The fixture declares its own launcher already.
                addJUnitPlatformLauncher.set(false)
                // Plain Temurin, never a JBR.
                jvmArgs.set(listOf("-Xmx2g"))
            }

            // PIT forks a JVM chosen by toolchain auto-detection, which can find a
            // JetBrains Runtime whose minion crashes ("Minion exited abnormally").
            // Pin it to plain Temurin, as the finding-13 oracle does.
            val toolchains = extensions.getByType(JavaToolchainService::class.java)
            tasks.withType<info.solidsoft.gradle.pitest.PitestTask>().configureEach {
                javaLauncher.set(
                    toolchains.launcherFor {
                        languageVersion.set(JavaLanguageVersion.of(25))
                        vendor.set(JvmVendorSpec.ADOPTIUM)
                    }
                )
            }
        }
    }
}
