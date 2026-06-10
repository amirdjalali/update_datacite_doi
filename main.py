import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from download_xml_records import download_oai_pmh_records
from extract_resource_elements import extract_resource_element
from validate_datacite_records import validate_all
from generate_report import generate_report
from update_datacite_DOIs import batch_create_dois

def load_config(config_path='config.json'):
    """
    Load configuration from JSON file
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        f.close()
    
    except FileNotFoundError:
        print(f"Configuration file {config_path} not found.")
        return None
    
    except json.JSONDecodeError:
        print(f"Invalid JSON in {config_path}")
        return None
    
    return config
    
def write_json(dict, file_path="config.json"):
    with open(file_path, "w") as f:
        json.dump(dict, f)
    f.close()
    
print(f"{"="*40}")
print(f"AlmaDL Utilities")
print(f"Update Datacite DOIS")
print(f"{"="*40}")
#print(f"Please enter config file [config.json]:", end=" ")
#config_path = input()
#if not config_path:

config_path = "config.json"
latest_path = "latest.json"
config = load_config(config_path)
latest = load_config(latest_path)
if not latest:
    print("Writing latest.json")
    latest = {}
    latest["latest_extracted_dir"] = ""

selection = 0

while selection != 4:

    print(f"Please select:")
    print(f"1. Download XML Records from OAI-PMH")
    print(f"2. Validate XML Records")
    print(f"3. Update DOIs")
    print(f"4. Exit")
    print(f"Enter your selection:", end=" ")

    selection = int(input())

    if selection == 1:
        print(f"Please enter your OAI-PMH base url [{config["oai_base_url"]}]:")
        oai_base_url = input()
        if not oai_base_url:
            oai_base_url = config["oai_base_url"]
        print(f"Please enter your destination directory [{config["downloaded_dir"]}]")
        downloaded_dir = input()
        if not downloaded_dir:
            downloaded_dir = config["downloaded_dir"]
        output_oai_dir = download_oai_pmh_records(oai_base_url, downloaded_dir)
        print(f"Records saved in {output_oai_dir}")
        output_resource_dir = extract_resource_element(config["extracted_dir"], output_oai_dir)
        print(f"Resource elements saved in {output_resource_dir}")
        latest["latest_extracted_dir"] = output_resource_dir
        write_json(latest, latest_path)

    elif selection == 2:
        print(f"Please enter <resource> element folder name [{latest["latest_extracted_dir"]}]", end=" ")
        input_resource_dir = input()
        if not input_resource_dir:
            input_resource_dir = latest["latest_extracted_dir"]
        validation_result_path = validate_all(input_resource_dir, config["logs_dir"])
        reports_path = generate_report(validation_result_path, config["logs_dir"])

    elif selection == 3:
        if config["test_doi_prefix"] != "":
            out_doi_prefix = config["test_doi_prefix"]
        else:
            out_doi_prefix = config["original_doi_prefix"]
        print(f"Updating or creating DOIs to {config["test_doi_prefix"]}, as {config["user"]}, using password {"*"*len(config["password"])}")
        print("Are your REALLY sure? Type YES to continue:", end=" ")
        reply = input()
        if reply == "YES":
            print(f"Enter your xml resource elements directory [{latest["latest_extracted_dir"]}]:")
            xml_dir = input()
            if not xml_dir:
                xml_dir = latest["latest_extracted_dir"]
            dois_created, dois_not_created = batch_create_dois(xml_dir, config["logs_dir"])
            print(f"Check the DOIs created report in {dois_created}")
            print(f"Check the DOIs not created report in {dois_not_created}")

    else:
        print("Please enter a number between 1 and 4")

print("Bye!!")