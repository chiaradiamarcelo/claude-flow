// Benchmark fixture for the pipeline-cost experiment.
//
// Deliberately NOT the same file as golden-repo-spring's: that fixture backs the
// finding-12 JPA evals and is pinned to Boot 4, whose JUnit Platform 6 cannot be
// driven by pitest-junit5. This one is pinned to Boot 3.5 / JUnit 5 so PIT runs
// natively over domain/ + application/ with no sidecar copy to drift.
//
// There is deliberately NO jacoco and NO pitest plugin here. The oracle is applied
// from ../oracle/oracle.init.gradle.kts at measurement time, so the pipeline's
// agents never see that the run is being scored — an agent that can read the
// mutation config could optimise for it, which would invalidate the arm.
plugins {
    kotlin("jvm") version "2.1.0"
    kotlin("plugin.spring") version "2.1.0"
    kotlin("plugin.jpa") version "2.1.0"
    id("org.springframework.boot") version "3.5.9"
    id("io.spring.dependency-management") version "1.1.7"
}

group = "com.example"
version = "0.0.1-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("org.springframework.boot:spring-boot-starter-validation")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin")
    runtimeOnly("com.h2database:h2")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation(kotlin("test"))
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

// Java-21 bytecode from a JDK-25 toolchain: PIT's bundled ASM cannot read class
// files newer than 21 (mutation-audit.md, carried from finding 14). Kotlin and
// javac both emit for the requested target regardless of the JDK running them,
// so this needs no second JDK installed.
kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

tasks.withType<JavaCompile>().configureEach {
    options.release.set(21)
}

tasks.test {
    useJUnitPlatform()
}
