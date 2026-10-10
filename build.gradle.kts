val locModustroRootBuildScript = file("gradle/tool/repository/modustro-root-build.gradle.kts")
if (locModustroRootBuildScript.isFile) {
    apply(from = locModustroRootBuildScript)
} else {
    apply(from = uri("https://raw.githubusercontent.com/Algites-EU/pub.gov.Algites/main/gradle/tool/repository/modustro-root-build.gradle.kts"))
}

apply(from = "gradle/generator-parity.gradle.kts")

apply(from = "gradle/sdocodegen-parity.gradle.kts")
