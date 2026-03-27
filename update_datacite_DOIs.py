import requests
import base64
import json
from lxml import etree
import os
import csv
from datetime import datetime
import calendar

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

def clean_doi(doi):
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    return doi

def extract_doi_prefix(doi):
    # Check if the DOI starts with "https://doi.org/"
    doi = clean_doi(doi)
    
    # Split the DOI by '/' and return the prefix (first part)
    prefix = doi.split('/')[0]
    return prefix

def prepare_datacite_doi_payload(config, xml_path):
    """
    Prepare payload for DOI creation using the XML resource
    
    :param xml_path: Path to the XML resource file
    :param prefix: DataCite DOI prefix (e.g., '10.xxxxx')
    :return: Dictionary with payload for DOI creation
    """

    test_doi_prefix = config["test_doi_prefix"]
    original_doi_prefix = config["original_doi_prefix"]

    # Parse the XML resource
    tree = etree.parse(xml_path)
    root = tree.getroot()

    # get id from record
    ns = {"datacite": "http://datacite.org/schema/kernel-4"}
    original_doi_elem = root.find(".//datacite:identifier[@identifierType='DOI']", namespaces=ns)
    
    if original_doi_elem is None:
        raise ValueError("No DOI identifier found in XML")

    original_doi = clean_doi(original_doi_elem.text.strip())

    print(f"Original DOI found: {original_doi}")

    prefix = extract_doi_prefix(original_doi)
    # Construct the full DOI
    if prefix == original_doi_prefix: # in case of DOIs already registered with DataCite
        full_doi = original_doi
        if test_doi_prefix != "": # if working in the test environment, replace original prefix with test prefix
            suffix = original_doi.replace(f"{original_doi_prefix}/", "")
            full_doi = f"{test_doi_prefix}/{suffix}"
    else:
        full_doi = original_doi

    
    print(f"Updating to {full_doi}")

    # Prepare the payload
    payload = {

        "data": {
            "type": "dois",
            "attributes": {
                "event": "publish",
                "doi": full_doi,
                "xml": None,
                "url": None
            }
        }    
    }

    # Add URL
    url_elem = root.find(".//datacite:alternateIdentifiers/datacite:alternateIdentifier[@alternateIdentifierType='URL']", namespaces=ns)
    
    if url_elem is not None:
        payload["data"]["attributes"]["url"] = url_elem.text

    return payload, full_doi

def create_doi(config, xml_path, xml_base64=True):
    """
    Create a DOI for a given XML resource
    
    :param xml_path: Path to the XML resource file
    :param username: DataCite API username
    :param password: DataCite API password
    :param xml_base64: Whether to include base64 encoded XML, default True
    :return: Created DOI or None if failed
    """
    
    username = config["user"]
    password = config["password"]
    url = config["api_base_url"]

    log = [] # for logging

    try:
        # Prepare payload for DOI metadata
        payload, full_doi = prepare_datacite_doi_payload(config, xml_path)

        # Optionally add base64 encoded XML
        if xml_base64:
            with open(xml_path, 'rb') as xml_file:
                xml_content = xml_file.read()
                payload['data']['attributes']['xml'] = base64.b64encode(xml_content).decode('utf-8')

        # Prepare headers
        headers = {
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }
        
        '''
        # Send POST request to create DOI
        response = requests.post(
            url,
            auth=(username, password),
            headers=headers,
            json=payload
        )
        '''

        # Send PUT request to update DOI
        # It creates new DOIs if the doi does not exist

        update_url = f"https://api.test.datacite.org/dois/{full_doi}"
        
        response = requests.put(
            update_url,
            json=payload,
            auth=(config["user"], config["password"]),
            headers={"Content-Type": "application/vnd.api+json"}
        )

        # Check response
        if response.status_code in [200, 201]:
            print(f"Successfully created DOI: {full_doi}")
            log = {
                "doi": full_doi,
                "Status code": response.status_code
            }
            return log
        else:
            print(f"Failed to create DOI. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            log = {
                "doi": full_doi,
                "Status code": response.status_code,
                "Response": response.json()
            }
            return log
        
    except Exception as e:
        print(f"Error creating DOI: {e}")
        return None
    
def batch_create_dois(config):
    """
    Create DOIs for all XML files in a directory
    
    :param xml_directory: Directory containing XML resource files
    :param prefix: DataCite DOI prefix
    :param username: DataCite API username
    :param password: DataCite API password
    """

    xml_directory = config["extracted_dir"]

    # Ensure the directory exists
    if not os.path.exists(xml_directory):
        print(f"Directory {xml_directory} does not exist.")
        return

    # Track created DOIs
    output = []
    not_created_dois = []

    # Iterate through XML files
    for root, dirs, files in os.walk(xml_directory):
        for filename in files:
            if filename.endswith('.xml'):
                xml_path = os.path.join(root, filename)

                try:
                    # Create DOI for each XML file
                    log = create_doi(config, xml_path)
                    if log:
                        output.append(log)
                
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    not_created_dois.append([filename, log["doi"], e])

    # Log created DOIs
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    dois_created_filename = f"logs/dois_created_{timestamp}.json"
    dois_not_created_filename = f"logs/dois_not_created_{timestamp}.json"

    with open(dois_created_filename, "w", encoding="UTF-8") as f:
        json.dump(output, f, indent=4)

    with open(dois_not_created_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["File", "DOI", "Error"])
        writer.writerows(not_created_dois)
    
# Usage example (commented out for safety)
# batch_create_dois(
#     xml_directory='path/to/extracted/resources', 
#     prefix='10.XXXXX',  # Your actual DataCite prefix
#     username='your_username', 
#     password='your_password'
# )

if __name__ == "__main__":
    config = load_config()
    if config:
        batch_create_dois(config)