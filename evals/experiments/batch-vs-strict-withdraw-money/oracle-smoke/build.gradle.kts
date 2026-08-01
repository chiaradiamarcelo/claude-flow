plugins {
    kotlin("jvm") version "2.1.0"
    kotlin("plugin.spring") version "2.1.0"
    kotlin("plugin.jpa") version "2.1.0"
    id("org.springframework.boot") version "4.0.4"
    id("io.spring.dependency-management") version "1.1.7"
    jacoco
    id("de.aaschmid.cpd") version "3.5"
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin")
    runtimeOnly("com.h2database:h2")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation(kotlin("test"))
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
    finalizedBy(tasks.jacocoTestReport)
}

// ---- Oracle: coverage (feeds CRAP) ----
jacoco {
    toolVersion = "0.8.12"
}
tasks.jacocoTestReport {
    dependsOn(tasks.test)
    reports {
        xml.required.set(true)
        html.required.set(true)
    }
}

// ---- Oracle: duplication (DRY) via PMD CPD (Kotlin tokenizer, decoupled from build Kotlin) ----
cpd {
    language = "kotlin"
    minimumTokenCount = 50
    isIgnoreFailures = true
    toolVersion = "7.7.0"
}
dependencies {
    "cpd"("net.sourceforge.pmd:pmd-kotlin:7.7.0")
}
tasks.named<de.aaschmid.gradle.plugins.cpd.Cpd>("cpdCheck") {
    reports {
        xml.required.set(true)
        text.required.set(false)
    }
    source = files("src/main/kotlin").asFileTree
}

// NOTE: mutation testing (PIT) does NOT run here. Spring Boot 4 forces JUnit Platform 6,
// which the pitest-junit5-plugin cannot drive (its coverage minion dies). PIT runs in the
// pure-Kotlin sidecar (oracle/pit-sidecar/) against the framework-free domain + application
// layers, which is where mutation testing has value anyway.
