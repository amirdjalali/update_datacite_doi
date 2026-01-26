import requests
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

def download_oai_pmh_records(config):
    base_url = config['oai_base_url']
    output_dir = config["downloaded_dir"]
    
    os.makedirs(output_dir, exist_ok=True)
    
    params = {
        'verb': 'ListRecords',
        'metadataPrefix': 'oai_datacite'
    }
    
    record_count = 0
    
    while True:
        try:
            # Make the request
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            # Parse the XML using lxml
            root = etree.fromstring(response.content)
            
            # Find all records
            records = root.findall('.//{http://www.openarchives.org/OAI/2.0/}record')
            
            for record in records:
                record_count += 1
                
                # Extract identifier for filename
                try:
                    identifier = record.find('.//{http://www.openarchives.org/OAI/2.0/}identifier').text
                    safe_filename = ''.join(c for c in identifier if c.isalnum() or c in ('-', '_')).rstrip()
                except AttributeError:
                    # Fallback filename if identifier can't be extracted
                    safe_filename = f'record_{record_count}'
                
                # Save the entire record as an XML file
                filename = os.path.join(output_dir, f'{safe_filename}.xml')
                
                # Convert the individual record to a pretty-printed XML string
                pretty_xml = etree.tostring(record, pretty_print=True, encoding='unicode')
                
                print(f"Downloading record {filename}")
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(pretty_xml)
            
            # Check for resumption token
            resumption_token = root.find('.//{http://www.openarchives.org/OAI/2.0/}resumptionToken')
            
            if resumption_token is not None and resumption_token.text:
                params = {
                    'verb': 'ListRecords',
                    'resumptionToken': resumption_token.text
                }
            else:
                break
        
        except requests.RequestException as e:
            print(f'Error downloading records: {e}')
            break
    
    print(f'Total records downloaded: {record_count}')

# Usage
if __name__ == "__main__":
    config = load_config()
    if config:
        download_oai_pmh_records(config)
