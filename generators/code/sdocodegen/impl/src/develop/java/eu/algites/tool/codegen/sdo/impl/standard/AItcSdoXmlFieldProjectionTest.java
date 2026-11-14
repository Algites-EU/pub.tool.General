package eu.algites.tool.codegen.sdo.impl.standard;

import org.testng.annotations.Test;
import eu.algites.lib.data.dataobject.*;
import eu.algites.lib.data.dataobject.xmldefs.*;
import eu.algites.lib.data.dataobject.xmlschema.*;
import eu.algites.lib.naming.convention.*;
import eu.algites.tool.codegen.sdo.impl.standard.*;
import java.util.*;
import java.util.regex.*;

/** Offline SDO generation regression, not committed to the source tree. */
/**
 * Regression for inherited schema-neutral getters and XML-specific covariant
 * projections. The generator now preserves XML binding annotations on the
 * mutable contract, while the XML format provider resolves nested implementations
 * through the purpose-scoped binding registry instead of static nested-type tables.
 *
 * @author linhart1
 */
public final class AItcSdoXmlFieldProjectionTest {
  /** Neutral metadata referenced by the parent but not XML-mapped. */
  @AIaDataObject public interface AIigSourceBindings_1 extends AIiDataObject {}
  /** Neutral nested child contract. */
  @AIaDataObject public interface AIigChild_1 extends AIiDataObject {
    /** @return neutral child name */
    @AIaDataObjectField String getName();
  }
  /** A shared DataObject with XML wire metadata on its own neutral getters. */
  @AIaDataObject
  @AIaDataObjectXmlSchema(namespace="urn:smoke",namespaceLocalName="Container")
  public interface AIigContainer_1 extends AIiDataObject {
    /** @return metadata bindings, which are deliberately not XML-mapped */
    @AIaDataObjectField AIigSourceBindings_1 getSourceBindings();
    /** @return nested child with XML field metadata */
    @AIaDataObjectField
    @AIaDataObjectFieldXmlSchema(namespaceLocalName="Child")
    AIigChild_1 getChild();
  }
  /** Neutral subclass inheriting the common annotation, narrowing an XML getter. */
  @AIaDataObjectXmlSchema(namespace="urn:smoke",namespaceLocalName="Derived")
  public interface AIigDerived_1 extends AIigContainer_1 {
    /** {@inheritDoc} */
    @Override @AIaDataObjectFieldXmlSchema(namespaceLocalName="SourceBindings")
    AIigSourceBindings_1 getSourceBindings();
  }
  /** Deterministic naming adapter isolating XML wire semantics from catalogs. */
  static final class Names implements AIiNameConventionCatalog {
    private final String mode;
    /** @param mode generated name family */
    Names(String mode) { this.mode=mode; }
    public Set<String> names() {return Set.of("common","xmldefs");}
    public String selectedRole(String role) {return role.startsWith("xmldefs") ? "xmldefs" : role.startsWith("common") ? "common" : role;}
    public String generatedMethodProfile() {return "smoke";}
    public String generatedMethodReference(String role) {return null;}
    public String generatedMethodLiteral(String role) {return switch(role) {
      case "multi_mapped_list_key_synthetic_getter" -> "_getKey";
      case "multi_mapped_list_value_synthetic_getter" -> "_getValue";
      default -> "";};}
    public String identifierConvention(String role,String structure) {return "upper_camel_case_1";}
    public boolean matches(String role,String structure,String value) {return true;}
    public Map<String,String> parse(String role,String structure,String source) {
      if (structure.equals("getter_method_name"))
        return Map.of("identifier",source.replaceFirst("^(get|is)",""),"version","1");
      if (!structure.equals("type_name")) throw new IllegalArgumentException("parse "+structure);
      Matcher m=Pattern.compile("(?:AIig|AIigd|AIcgd)([A-Za-z0-9]+)_([0-9]+)").matcher(source);
      if (!m.matches()) throw new IllegalArgumentException("bad name: "+source+" / "+role);
      return Map.of("identifier",m.group(1),"version",m.group(2));
    }
    public String format(String role,String structure,Map<String,String> vars,String from) {
      String id=vars.get("identifier"),version=vars.getOrDefault("version","1");
      String prefix="";
      return switch(structure){
        case "type_name" -> (mode.equals("mutable")?"AIigd":"AIcgd")+prefix+id+"_"+version;
        case "file_name_stem" -> (mode.equals("mutable")?"AIigd":"AIcgd")+prefix+id+"_"+version;
        case "file_name_suffix" -> ".java";
        case "getter_method_name" -> "get"+id;
        case "setter_method_name" -> "set"+id;
        case "method_parameter_name" -> "a"+id;
        case "raw_getter" -> "_getRaw_"+id;
        case "raw_presence_checker_method" -> "_isPresent_"+id;
        case "raw_unsetter" -> "_unset_"+id;
        default -> throw new IllegalArgumentException("format "+structure);
      };
    }
  }
  /** Check independently annotated XML wire metadata on neutral Java contracts. */
  @Test
  public void explicitXmlFieldsOnly() {
    var generator=new AIcSdoCodegenService();
    var result=generator.generate(AIigContainer_1.class,"gd",
      new Names("input"),new Names("mutable"),new Names("concrete"),"intf","impl");
    var source=result.implementation().source();
    var mutable=result.mutableInterface().source();
    if (source.contains("xmlNestedTypes()"))
      throw new AssertionError("New SDO must not generate static nested concrete maps");
    if (!mutable.contains("AIaDataObjectFieldXmlSchema(")
        || !mutable.contains("namespaceLocalName = \"Child\""))
      throw new AssertionError("Missing XML field annotation on mutable contract: " + mutable);
    if (source.contains("Map.entry(\"SourceBindings\""))
      throw new AssertionError("Common non-XML getter was treated as XML element");
    var neutralNested = generator.generate(AIigDerived_1.class,"gd",new Names("input"),
      new Names("mutable"),new Names("concrete"),"intf","impl");
    if (!neutralNested.mutableInterface().source().contains("namespaceLocalName = \"SourceBindings\""))
      throw new AssertionError("Schema-neutral child lost explicit XML wire metadata");
    if (neutralNested.implementation().source().contains("xmlNestedTypes()"))
      throw new AssertionError("XML wire metadata must not link to concrete nested implementations");
    System.out.println("PASS: XML projections");
  }
}
