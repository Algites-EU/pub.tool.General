"""Qualified type identities from General are independent of AAC binding formatting."""
from pathlib import Path

from eu.algites.lib.naming.convention.aic_algites_naming_profiles import AIcAlgitesNamingProfiles
from eu.algites.tool.codegen.defs.aic_json_schema_reader import AIcJsonSchemaReader
from eu.algites.tool.codegen.defs.aic_schema_contract_interface_generator import AIcSchemaContractInterfaceGenerator
from eu.algites.tool.codegen.defs.aicd_definition_load_request import AIcdDefinitionLoadRequest
from eu.algites.tool.codegen.defs.aicd_code_generation_request import AIcdCodeGenerationRequest
from eu.algites.tool.codegen.defs.ain_definition_source_kind import AInDefinitionSourceKind
from eu.algites.tool.codegen.defs.ain_code_generation_target import AInCodeGenerationTarget
from eu.algites.tool.codegen.defs.ain_defs_name_role import AInDefsNameRole


def test_python_java_schema_contract_identities():
    schema = {
        'x-aac-schema-id': '_A.test.example', 'x-aac-schema-version': 2,
        'type': 'object', 'properties': {'Name': {'type':'string'}},
    }
    reader=AIcJsonSchemaReader()
    for target, ext in ((AInCodeGenerationTarget.PYTHON,'.py'),(AInCodeGenerationTarget.JAVA,'.java')):
        profile=(AIcAlgitesNamingProfiles.python_profile() if target is AInCodeGenerationTarget.PYTHON
                 else AIcAlgitesNamingProfiles.java_profile())
        load=AIcdDefinitionLoadRequest(Path('example_2.json'),AInDefinitionSourceKind.JSONDEFS,profile)
        definition=reader.read(schema,load,AInDefinitionSourceKind.JSONDEFS,
                               'x-aac-schema-id','x-aac-schema-version','x-jsondefs-name')
        request=AIcdCodeGenerationRequest(definition,target,'eu.algites.example',profile)
        source=AIcSchemaContractInterfaceGenerator().generate(request)
        identity=source.primary_type
        assert identity.type_name==source.type_name
        assert identity.type_role is AInDefsNameRole.INTERFACE_TYPE
        assert identity.source_definition_id == '_A.test.example'
        assert identity.source_definition_version == 2
        assert identity.namespace == 'eu.algites.example'
        assert identity.technology_kind is target
        assert identity.fully_qualified_type_name.endswith('.'+source.type_name)
        if ext=='.py':
            assert identity.module_name=='eu.algites.example.'+source.relative_path.rsplit('/',1)[-1][:-3]
        else:
            assert identity.module_name == 'eu.algites.example'
