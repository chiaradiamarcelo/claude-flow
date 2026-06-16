// Framework-free Kotlin core for the developer-integration eval (finding 07).
// Plain Kotlin + JUnit5 — NO Spring, NO JPA, NO DB — so the developer agent's
// generated domain/use-case/fake/contract code compiles and runs fast.
plugins {
    kotlin("jvm") version "2.1.0"
}

repositories {
    mavenCentral()
}

dependencies {
    testImplementation(kotlin("test"))
}

tasks.test {
    useJUnitPlatform()
}
