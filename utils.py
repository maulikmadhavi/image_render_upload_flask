from PIL import Image

class Model:
    def __init__(self) -> None:        
        print("***************** Model initialized ******************" )

    def get_info(self, file_path):
        image = Image.open(file_path)
        width, height = image.size
        return width, height