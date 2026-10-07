import groovy.json.JsonOutput
import org.gradle.api.provider.ListProperty
import org.gradle.api.tasks.testing.Test

/* Java integration tests invoke the independent Python implementation with its declared dependencies. */
val locGeneratorCoreImpl = project(":generators:code:defscodegen:coreimpl")
val locGeneratorCoreIntf = project(":generators:code:defscodegen:coreintf")
val locParityPythonDirectory = layout.buildDirectory.dir("run/generator-parity/python-dependencies")
val locPythonExecutable = providers.environmentVariable("ALGITES_PYTHON_EXECUTABLE").getOrElse("python3")
val locParityPreparationScript = layout.projectDirectory.file("generators/code/defscodegen/prepare_parity_python.py")
val locParityMetadata = listOf(locGeneratorCoreIntf, locGeneratorCoreImpl).map { it.layout.projectDirectory.file("pyproject.toml") }
val locParityRefreshDependencies = gradle.startParameter.isRefreshDependencies
@Suppress("UNCHECKED_CAST")
val locParityEndpoints = (locGeneratorCoreImpl.tasks.named("resolvePythonDependencies").get().property("endpointDefinitions") as ListProperty<String>).get()
val locPrepareGeneratorParityPython = tasks.register<Exec>("prepareModustroGeneratorParityPython") {
    group = "verification"
    description = "Prepares isolated declared Python dependencies for cross-implementation generator tests."
    dependsOn(locGeneratorCoreIntf.tasks.named("generatePythonProjectMetadata"), locGeneratorCoreImpl.tasks.named("generatePythonProjectMetadata"))
    inputs.files(locParityMetadata)
    inputs.file(locParityPreparationScript)
    inputs.property("pythonExecutable", locPythonExecutable)
    inputs.property("publicSubscriptions", locParityEndpoints)
    outputs.dir(locParityPythonDirectory)
    val locRefreshDependencies = locParityRefreshDependencies
    outputs.upToDateWhen { !locRefreshDependencies }
    commandLine(listOf(locPythonExecutable, locParityPreparationScript.asFile.absolutePath,
        "--target", locParityPythonDirectory.get().asFile.absolutePath,
        "--endpoints-json", JsonOutput.toJson(locParityEndpoints))
        + locParityMetadata.flatMap { listOf("--metadata", it.asFile.absolutePath) })
}
locGeneratorCoreImpl.tasks.withType<Test>().configureEach {
    dependsOn(locPrepareGeneratorParityPython)
    inputs.files(locGeneratorCoreIntf.layout.projectDirectory.dir("src/product/python"),
        locGeneratorCoreImpl.layout.projectDirectory.dir("src/product/python"),
        locGeneratorCoreImpl.layout.projectDirectory.dir("src/develop/python"))
    inputs.dir(locParityPythonDirectory)
    environment("MODUSTRO_GENERATOR_PARITY_PYTHON_DEPENDENCIES", locParityPythonDirectory.get().asFile.absolutePath)
}
