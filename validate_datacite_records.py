import os
from lxml import etree
import urllib.request
from datetime import datetime
import json

# The W3C xml.xsd defines the built-in xml:lang / xml:space / xml:base attributes.
# lxml does NOT bundle this, so any DataCite schema that references xml:lang will
# raise XMLSchemaParseError unless we download xml.xsd and point lxml at it via a
# custom resolver.
W3C_XML_XSD_URL = "https://www.w3.org/2001/xml.xsd"
W3C_XML_XSD_NAMESPACE = "http://www.w3.org/XML/1998/namespace"

class LocalResolver(etree.Resolver):
    """Redirect any request for the W3C xml namespace to our local copy."""
    def __init__(self, schema_dir):
        self.xml_xsd_path = os.path.abspath(os.path.join(schema_dir, "xml.xsd"))

    def resolve(self, url, id, context):
        if url == W3C_XML_XSD_NAMESPACE or url == W3C_XML_XSD_URL:
            return self.resolve_filename(self.xml_xsd_path, context)
        return None

def download_xsd(schema_dir, base_url, path, visited=None):
    if visited is None:
        visited = set()

    if path in visited:
        return
    visited.add(path)
    print(f"Processing schema: {path}")

    url = (base_url + path).replace(os.sep, "/")  # Ensure consistent path separators
    local_path = os.path.join(schema_dir, path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    print(f"Downloading: {url}")
    urllib.request.urlretrieve(url, local_path)

    # Parse and recurse into any xs:include / xs:import entries
    tree = etree.parse(local_path)
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    for inc in tree.findall(".//*[@schemaLocation]", ns):
        inc_path = inc.get("schemaLocation")
        # Skip external namespace imports (e.g. the W3C xml.xsd — handled separately)
        if inc_path.startswith("http"):
            continue
        current_dir = os.path.dirname(path)
        resolved = os.path.normpath(os.path.join(current_dir, inc_path))
        download_xsd(schema_dir, base_url, resolved, visited)

def validate_all(xml_dir, out_dir="logs/", schema_dir="schema", base_url="https://schema.datacite.org/meta/kernel-4/"):

    download_xsd(schema_dir.replace("/", os.sep), base_url, "metadata.xsd")

    # Download the W3C xml.xsd so lxml can resolve xml:lang references
    xml_xsd_local = os.path.join(schema_dir, "xml.xsd")
    if not os.path.exists(xml_xsd_local):
        print(f"Downloading: {W3C_XML_XSD_URL}")
        urllib.request.urlretrieve(W3C_XML_XSD_URL, xml_xsd_local)
    print("Done! All schema files downloaded.")

    # Build an XMLParser with our custom resolver so lxml finds xml.xsd locally
    parser = etree.XMLParser()
    parser.resolvers.add(LocalResolver(schema_dir))

    schema_path = os.path.join(schema_dir, "metadata.xsd")
    with open(schema_path, 'rb') as f:
        schema = etree.XMLSchema(etree.parse(f, parser))

    os.makedirs(out_dir, exist_ok=True)

    results = {}
    for filename in os.listdir(xml_dir):
        if filename.endswith(".xml"):
            xml_path = os.path.join(xml_dir, filename)
            try:
                xml_doc = etree.parse(xml_path)
                valid = schema.validate(xml_doc)
                errors = [f"Line {e.line}: {e.message}" for e in schema.error_log]
                results[filename] = {"valid": valid, "errors": errors}
            except etree.XMLSyntaxError as e:
                results[filename] = {"valid": False, "errors": [f"Malformed XML: {e}"]}

    out_path = os.path.join(out_dir, ("validation_results_" + xml_dir[-19:] + ".json"))
    with open(out_path, "w", encoding="UTF-8") as out_file:
        json.dump(results, out_file, indent=4)

    print(f"Validation complete. Results written to: {out_path}")
    return out_path

if __name__ == "__main__":
    validate_all(os.path.join("tests", "selected_xml_resources_2026-06-09_12-40-00"), "schema/", "https://schema.datacite.org/meta/kernel-4/", "logs/")