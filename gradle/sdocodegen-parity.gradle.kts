import groovy.json.JsonOutput
import org.gradle.api.provider.ListProperty
import org.gradle.api.tasks.testing.Test

/* Native Python SDO tests share the verification lifecycle with their Java counterpart. */
val locSdoIntf = project(":generators:code:sdocodegen:intf")
val locSdoImpl = project(":generators:code:sdocodegen:impl")
val locSdoPythonDirectory = layout.buildDirectory.dir("run/sdo-parity/python-dependencies")
val locSdoPythonExecutable = providers.environmentVariable("ALGITES_PYTHON_EXECUTABLE").getOrElse("python3")
val locSdoPreparationScript = layout.projectDirectory.file("generators/code/defscodegen/prepare_parity_python.py")
val locSdoMetadata = listOf(locSdoIntf, locSdoImpl).map { it.layout.projectDirectory.file("pyproject.toml") }
val locSdoRefreshDependencies = gradle.startParameter.isRefreshDependencies
@Suppress("UNCHECKED_CAST")
val locSdoEndpoints = (locSdoImpl.tasks.named("resolvePythonDependencies").get()
    .property("endpointDefinitions") as ListProperty<String>).get()
val locPrepareSdoParityPython = tasks.register<Exec>("prepareModustroSdoParityPython") {
    group = "verification"
    description = "Prepares Python SmartDataObject runtime and generator verification dependencies."
    dependsOn(locSdoIntf.tasks.named("generatePythonProjectMetadata"),
        locSdoImpl.tasks.named("generatePythonProjectMetadata"))
    inputs.files(locSdoMetadata)
    inputs.file(locSdoPreparationScript)
    inputs.property("pythonExecutable", locSdoPythonExecutable)
    inputs.property("publicSubscriptions", locSdoEndpoints)
    outputs.dir(locSdoPythonDirectory)
    outputs.upToDateWhen { !locSdoRefreshDependencies }
    commandLine(listOf(locSdoPythonExecutable, locSdoPreparationScript.asFile.absolutePath,
        "--target", locSdoPythonDirectory.get().asFile.absolutePath,
        "--endpoints-json", JsonOutput.toJson(locSdoEndpoints),
        "--requirement", "pytest>=8,<10", "--requirement", "pyyaml>=6,<7")
        + locSdoMetadata.flatMap { listOf("--metadata", it.asFile.absolutePath) })
}
locSdoImpl.tasks.withType<Test>().configureEach {
    dependsOn(locPrepareSdoParityPython)
    inputs.files(locSdoIntf.layout.projectDirectory.dir("src/product/python"),
        locSdoImpl.layout.projectDirectory.dir("src/product/python"),
        locSdoImpl.layout.projectDirectory.dir("src/develop/python"),
        layout.projectDirectory.dir("generators/code/defscodegen/intf/src/product/python"),
        layout.projectDirectory.dir("generators/code/defscodegen/impl/src/product/python"))
    inputs.dir(locSdoPythonDirectory)
    environment("MODUSTRO_SDO_PYTHON_DEPENDENCIES", locSdoPythonDirectory.get().asFile.absolutePath)
}
