import os
import shutil
import json
from lxml import etree

def sort_by_resource_type(input_dir):

    # check if the file with sorted records exists, otherwise do nothing
    if not os.path.exists("all_records.json"):
        print("Starting to sort records by resourceType")
        print(f"Selecting items from dir {input_dir}")
        files_per_type = {}
        # Process each file in the input directory and add to the dictionary
        for filename in os.listdir(input_dir):
            print(f"Processing file {filename}")
            if filename.endswith('.xml'):
                input_path = os.path.join(input_dir, filename)
            
                try:
                    # Parse the XML file
                    with open(input_path, 'rb') as f:
                        tree = etree.parse(f)
                        root = tree.getroot()
                    
                        # Define namespaces
                        namespace = {
                            'datacite': 'http://datacite.org/schema/kernel-4'
                        }

                        # Find type and add file in dictionary per type
                        resource_type = root.find('.//datacite:resourceType', namespace)
                        if resource_type is not None:
                            resource_type_general = resource_type.get('resourceTypeGeneral')
                            if resource_type_general is not None and resource_type_general not in files_per_type:
                                files_per_type[resource_type_general] = list()
                            files_per_type[resource_type_general].append(filename)
                
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
        
        print("Saving sorted records in all_records.json")
        with open("all_records.json", "w") as f:
            json.dump(files_per_type, f, indent=4)
    
    else:
        print("Records were already sorted by resourceType!")
        with open("all_records.json", "r") as f:
            files_per_type = json.load(f)
    
    return files_per_type
    
def select_by_amount(files_per_type, amount):

    if not os.path.exists("selected_records.json"):

        selected_files = {}

        for resource_type in list(files_per_type):
            number_of_files = len(files_per_type[resource_type])
            step = number_of_files//amount
            files_per_type[f"{resource_type}_selected"] = list()
            selected_files[resource_type] = []
            for i in range(0, number_of_files, step):
                #print(i)
                #print(files_per_type[resource_type][i])
                selected_files[resource_type].append(files_per_type[resource_type][i])
        print("Saving selected records in selected_records.json")
        with open("selected_records.json", "w") as f:
            json.dump(selected_files, f, indent=4)
    
    else:
        print("Files were already selected, and already stored in selected_records.json")
        with open("selected_records.json", "r") as f:
            selected_files = json.load(f)
    
    return selected_files

def copy_selected_files(selected_files, input_dir, output_dir):

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for type in selected_files:
        type_dir = os.path.join(output_dir, type)
        try:
            os.makedirs(type_dir, exist_ok=True)
        except OSError as e:
            print(f"Failed to create directory for: {type!r}")
            print(f"Path attempted: {type_dir!r}")
            print(f"Files contained in this type: {selected_files[type]}")
            print(f"Error: {e}") 
    
    for type in selected_files:
        print(f"Copying records of resourceType {type}")
        type_dir = os.path.join(output_dir, type)
        for filename in selected_files[type]:
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(type_dir, filename)
            print(f"Copying {input_path} into {output_path}")
            shutil.copy(input_path, output_path)

if __name__ == "__main__":

    input_dir = "tests/extracted_xml_resources_all"
    output_dir = "tests/selected_xml_resources"
    files_dict = sort_by_resource_type(input_dir)
    selected_files = select_by_amount(files_dict, 10)
    copy_selected_files(selected_files, input_dir, output_dir)