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
    implementation("org.springframework.boot:spring-boot-starter-flyway")
    runtimeOnly("com.h2database:h2")
    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.springframework.boot:spring-boot-starter-webmvc-test")
    testImplementation("org.springframework.boot:spring-boot-starter-data-jpa-test")
    testImplementation(kotlin("test"))
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
}

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
