# Update DOI metadata in DataCite

This repository contains scripts to update the metadata of DOIs registered with [https://support.datacite.org/docs/api-create-dois](DataCite).

In order to work, it needs a ```config.json``` [configuration](#configuration) file.

## ```download_xml_records.py``` 

The script downloads the current metadata from an OAI-PMH interface (```oai_base_url```), and saves them in separate xml files in the ```downloaded_dir``` folder.

## ```extract_resource_elements.py```

In case the metadata are exposed in the ```oai_datacite``` metadata schema, you might want to keep only the ```<resource>``` element in the records contained in the ```downloaded_dir``` folder. Use the ```extract_resource_elements.py``` script to do that.

## ```validate_datacite_records.py```

Validates DataCite metadata against the DataCite schema and logs the results. Usage:

```
validate_all(<path to schema dir>, <path to resource xml folder>, "https://schema.datacite.org/meta/kernel-4/", <path to log folder>)
```

## ```generate_report.py```

Looks for the ```validation_results.json``` file within the ```logs/``` folder and creates a neat report grouping records with the same validation errors.

## ```update_datacite_DOIs.py``` 

The script updates the metadata of the DOIs in DataCite using the DataCite REST API, picking xml records from the ```extracted_dir``` folder. It sends a PUT request:

```python
    response = requests.put(
                update_url,
                json=payload,
                auth=(config["user"], config["password"]),
                headers={"Content-Type": "application/vnd.api+json"}
            )
```

where ```payload``` is a dictionary with the following strcuture:

```python
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
```

the ```xml``` value contains the base-64 encoding of the record to update. ```url``` is parsed from the record's XML.

If working in the test environment, update your ```config.json``` file by adding your DataCite test DOI prefix and original DataCite DOI prefix.

The script parses each record finding the record's original DOI. If the DOI is a DataCite DOI (if its prefix corresponds to ```original_doi_prefix```), then it substitutes the original prefix with the ```test_doi_prefix``` (if specified). Otherwise, the script tries to update the record using the original DOI.

## Prerequisites

- Python 3.x
- Works with the following Python packages: requests 2.32.5, lxml 6.0.2
- DataCite account with API access

## Configuration

To run the script you need to create a configuration file ```config.json``` in the root folder.

The ```config.json``` file should look like this:

```json
{
    "oai_base_url": "<your OAI-PMH base URL>",
    "api_base_url": "<https://api.test.datacite.org/dois> or <https://api.datacite.org/dois>",
    "downloaded_dir": "oai_xml_records",
    "extracted_dir": "extracted_xml_resources",
    "test_doi_prefix": "your test DOI prefix, without /. Add only if you are working in the test environment",
    "original_doi_prefix": "your original DOI prefix, without /. Add only if you are working in the test environment",
    "user": "<your DataCite username>",
    "password": "<your DataCite password>"
}
```