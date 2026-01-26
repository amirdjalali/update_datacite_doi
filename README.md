# Update DOI metadata in DataCite

This repository contains scripts to update the metadata of DOIs registered with DataCite.

```download_xml_records.py``` downloads the current metadata of AMS Acta DOIs through the OAI-PMH interface, and saves them in separate xml files.

```extract_resource_elements.py``` extracts the ```<resource>``` elements from the records downloaded with ```download_xml_records.py```, in case the metadata are exposed in the oai_datacite metadata schema.

```update_doi_metadata.py``` updates the metadata of the DOIs in DataCite using the DataCite REST API.

## Prerequisites

- Python 3.x
- Required Python packages: requests, xml.etree.ElementTree, lxml
- DataCite account with API access

## Configuration

To run the script you need to set up a configuration file ```config.json``` containing the output folder names and your DataCite API credentials.

The config file should look like this:

```json
{
    "oai_base_url": "<your OAI-PMH base URL>",
    "api_base_url": "<https://api.test.datacite.org/dois> or <https://api.datacite.org/dois>",
    "downloaded_dir": "oai_xml_records",
    "extracted_dir": "extracted_xml_resources",
    "doi_prefix": "<your DOI prefix>",
    "user": "<your DataCite username>",
    "password": "<your DataCite password>"
}
```