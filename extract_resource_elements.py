import os
import json
from lxml import etree

def load_config(config_path='config.json'):
    """
    Load configuration from JSON file
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    
    except FileNotFoundError:
        print(f"Configuration file {config_path} not found.")
        return None
    
    except json.JSONDecodeError:
        print(f"Invalid JSON in {config_path}")
        return None

def extract_resource_element(config):
    """
    Extract only the <resource> element from OAI-PMH XML files.
    
    Args:
        config (dict): Configuration dictionary containing directories.
    """
   
    input_dir = config["downloaded_dir"]
    output_dir = config["extracted_dir"]

    print(input_dir)
    print(output_dir)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each file in the input directory
    for filename in os.listdir(input_dir):
        if filename.endswith('.xml'):
            input_path = os.path.join(input_dir, filename)
            
            try:
                # Parse the XML file
                with open(input_path, 'rb') as f:
                    tree = etree.parse(f)
                    root = tree.getroot()

                    # Define namespaces
                    namespaces = {
                        'oai': 'http://www.openarchives.org/OAI/2.0/',
                        'datacite': 'http://schema.datacite.org/oai/oai-1.0/',
                        'kernel': 'http://datacite.org/schema/kernel-4'
                    }
                    
                    # Find the resource element considering its namespace
                    resource_elem = root.find('.//kernel:resource', namespaces)

                    if resource_elem is None:
                        print(f"No resource element found in {filename}")
                        continue
                    
                    # Convert to string and pretty print
                    pretty_xml = etree.tostring(resource_elem, pretty_print=True, encoding='unicode')

                    # Save the extracted resource element
                    output_path = os.path.join(output_dir, filename)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(pretty_xml)
                    
                    print(f'Extracted resource from: {filename}')
            
            except Exception as e:
                print(f"Error processing {filename}: {e}")

# Usage
if __name__ == "__main__":
    config = load_config("config.json")
    extract_resource_element(config)
