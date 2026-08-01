import info.solidsoft.gradle.pitest.PitestTask

plugins {
    kotlin("jvm") version "2.1.0"
    id("info.solidsoft.pitest") version "1.19.0"
}

repositories {
    mavenCentral()
}

dependencies {
    testImplementation(kotlin("test"))
    testImplementation(platform("org.junit:junit-bom:5.13.4"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

// Java 21 bytecode so PIT's bundled ASM (9.7.1, max Java 23) can read the classes,
// even though the JDK running the build is Temurin 25.
kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
    }
}
tasks.withType<JavaCompile>().configureEach { options.release.set(21) }

tasks.test { useJUnitPlatform() }

pitest {
    junit5PluginVersion.set("1.2.2")
    pitestVersion.set("1.19.1")
    targetClasses.set(listOf("com.example.bank.domain.*", "com.example.bank.application.*"))
    targetTests.set(listOf("com.example.bank.*"))
    outputFormats.set(listOf("XML", "HTML"))
    timestampedReports.set(false)
    threads.set(2)
}

// PIT forks its own JVM chosen by toolchain auto-detection, which finds Android Studio's
// JBR (Java 21) — whose forked minion crashes. Pin PIT to a plain Temurin JDK.
tasks.withType<PitestTask>().configureEach {
    javaLauncher.set(
        javaToolchains.launcherFor {
            languageVersion.set(JavaLanguageVersion.of(25))
            vendor.set(JvmVendorSpec.ADOPTIUM)
        }
    )
}
