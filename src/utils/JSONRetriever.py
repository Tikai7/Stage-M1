import os
import requests
import json

class JSONRetriever:
    """
    Class to retrieve images from JSON files.
    """
    @staticmethod
    def get_images_from_json(path, dest_path):
        """
        Get images from JSON files in the field 'related'.
        @param path: The path to the JSON files.
        @param dest_path: The path to save the images.
        """
        json_files = os.listdir(path)
        for file in json_files:
            with open(os.path.join(path, file), 'r') as f:
                data = json.load(f)
                url = data['related']
                image_url = url + "/f1.highres"
                image_name = image_url.split("/")[-2]
                img_data = requests.get(image_url).content
                with open(os.path.join(dest_path, f'{image_name}.jpg'), 'wb') as handler:
                    handler.write(img_data)