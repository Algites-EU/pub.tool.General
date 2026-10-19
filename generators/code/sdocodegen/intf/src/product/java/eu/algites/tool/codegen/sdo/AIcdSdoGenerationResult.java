package eu.algites.tool.codegen.sdo;

/**
 * The independent mutable interface and concrete implementation generated from one read contract.
 *
 * @param mutableInterface generated mutable contract
 * @param implementation generated concrete SmartDataObject implementation
 */
public record AIcdSdoGenerationResult(AIcdGeneratedSdoSource mutableInterface,
        AIcdGeneratedSdoSource implementation) { }
