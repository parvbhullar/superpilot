# Script to genarate youtube thumnails from text 
import os
import requests
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from transformers import CLIPProcessor, CLIPModel
import numpy as np
import cv2


# Load environment variables from .env file
load_dotenv()

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Class to genarate thumbnails using replacing the background
class ThumbnailGenarator():
    """
    Class to genarate thumbnails using replacing the background 
    Args:
        image_path: path to the image
        backgoround_prompt: prompt for the background
        text_prompt: prompt for the text
        font: font to use for the text
        text: text to use for the text
        remove_background_flag: flag to remove background or not
    
    """
    def __init__(self,image_path, backgoround_prompt, text_prompt, font, overlaid_text, remove_background_flag = False,expand_dim = None):
        self.image_path = image_path
        self.backgoround_prompt = backgoround_prompt
        self.text_prompt = text_prompt
        self.font = font
        self.overlaid_text = overlaid_text
        self.remove_background_flag = remove_background_flag
        self.remove_background_url = os.getenv("REMOVE_BACKGROUND_URL")
        self.url_replace_background = os.getenv("REPLACE_BACKGROUND_URL")
        self.x_api_key = os.getenv("CLIPDROP_API_KEY")
        self.phot_x_api_key = os.getenv("PHOTAI_API_KEY")
        self.url_genarate_background = os.getenv("GENARATE_BACKGROUND_URL")
        self.expand_dim = expand_dim

    # if the image is not in 16:9 aspect ratio, calculates the pixels to add in which dimension
    def calculate_pixels_to_add(self,image_path):
        # Open the image
        with Image.open(image_path) as img:
            # Get the current width and height of the image
            width, height = img.size

            # Calculate the current aspect ratio
            current_aspect_ratio = width / height

            # Check if the aspect ratio is 16:9
            if abs(current_aspect_ratio - 16 / 9) < 0.01:
                print("The image already has a 16:9 aspect ratio.")
                return 0, None

            # Calculate the target width and height for a 16:9 aspect ratio
            target_width = int(16 / 9 * height)
            target_height = int(9 / 16 * width)

            # Check which dimension needs adjustment
            if current_aspect_ratio < 16 / 9:
                # Add pixels to the right
                pixels_to_add = target_width - width
                return pixels_to_add, "width"
            else:
                # Add pixels to the bottom
                pixels_to_add = target_height - height
                return pixels_to_add, "height"

    def check_host(self,image_path):
        image = Image.open(image_path)

        inputs = processor(text=["a person present","person is not present"], images=image, return_tensors="pt", padding=True)

        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image  # this is the image-text similarity score
        probs = logits_per_image.softmax(dim=1)  # we can take the softmax to get the label probabilities
        if probs.argmax().item() == 1:
            return False
        else:
            return True

    # to uncrop the image if the image is not in 16:9 aspect ratio      
    def uncrop(self,image_path,left_pad,right_pad,top_pad,bottom_pad):
        headers = {
            'x-api-key': self.x_api_key,
        }

        files = {
            'image_file': (image_path, open(image_path, 'rb')),
        }

        data = { 'extend_left': left_pad, 'extend_right' : right_pad, 'extend_up' : top_pad, 'extend_down' : bottom_pad}
        tmp_image_name = 'uncrop.jpg'
        response = requests.post('https://clipdrop-api.co/uncrop/v1', headers=headers, files=files, data=data)
        if response.status_code == 200:
            with open(tmp_image_name, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception("Error in uncropping the background, response code: {}".format(response.status_code))
        return tmp_image_name
        

    def add_white_pixels_to_image(self,image_path, left_pad, right_pad, top_pad, bottom_pad):
        """Adds white pixels to the specified image edges.

        Args:
            image_path (str): Path to the input image.
            left_pad (int): Number of white pixels to add on the left.
            right_pad (int): Number of white pixels to add on the right.
            top_pad (int): Number of white pixels to add on the top.
            bottom_pad (int): Number of white pixels to add on the bottom.

        Raises:
            ValueError: If any padding value is negative.
        """

        image = cv2.imread(image_path)

        if any(pad < 0 for pad in (left_pad, right_pad, top_pad, bottom_pad)):
            raise ValueError("Padding values cannot be negative.")

        height, width, channels = image.shape

        # Ensure white pixels have values (255, 255, 255) across channels
        white_color = (255, 255, 255) * np.ones(shape=(1, 1, channels), dtype=np.uint8)

        # Create enlarged canvas with padded pixels
        padded_image = np.zeros(
            shape=(height + top_pad + bottom_pad, width + left_pad + right_pad, channels),
            dtype=np.uint8
        )
        padded_image[:] = white_color

        # Place original image in the center of the canvas
        start_y = top_pad
        end_y = start_y + height
        start_x = left_pad
        end_x = start_x + width

        padded_image[start_y:end_y, start_x:end_x] = image
        output_path = 'padded_image.jpg'
        cv2.imwrite(output_path, padded_image)
        return output_path


    # to genarate the image
    def genarate_image(self,prompt):
        headers = {
            'x-api-key': self.x_api_key,
        }
        files = {
        'prompt': (None, prompt + str(" ,youtube thumbnail style"), 'text/plain')
        }
        tmp_image_name = 'genarated_background.jpg'
        response = requests.post(self.url_genarate_background, headers=headers, files=files)
        if response.status_code == 200:
            with open(tmp_image_name, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception("Error in genarating the background, response code: {}".format(response.status_code))
        return tmp_image_name

    # to remove background
    def remove_background(self,image_path):
        headers = {
            'x-api-key': self.x_api_key,
        }

        files = {
            'image_file': (image_path, open(image_path, 'rb')),
        }
        tmp_image_name = 'removed_background.jpg'
        response = requests.post(self.remove_background_url, headers=headers, files=files)
        if response.status_code == 200:
            with open(tmp_image_name, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception("Error in removing the background, response code: {}".format(response.status_code))
        return tmp_image_name
    

    # to fill the background by replacing it
    def background_fill(self,image_path,backgoround_prompt):
        # print("self.x_api_key",self.x_api_key)
        headers = {
            'x-api-key': self.x_api_key,
        }

        files = {
            'image_file': (image_path, open(image_path, 'rb')),
        }

        data = {
            'prompt': backgoround_prompt,
        }
        tmp_image_name = 'updated_background_image.jpg'
        response = requests.post(self.url_replace_background, headers=headers, files=files, data=data)
        if response.status_code == 200:
            with open(tmp_image_name, 'wb') as f:
                f.write(response.content)
        elif response.status_code == 422:
            prompt = backgoround_prompt + str(" ,youtube thumbnail style")
            tmp_image_name = self.genarate_image(prompt)
            try:
                pixels, dimension = self.calculate_pixels_to_add(tmp_image_name)
            except Exception as e:
                raise Exception("Error in calculating the pixels to add, {}".format(e))
            if pixels > 0:
                if dimension == "width":
                    left_pad = pixels // 2
                    right_pad = pixels - left_pad
                    top_pad = 0
                    bottom_pad = 0
                else:
                    top_pad = pixels // 2
                    bottom_pad = pixels - top_pad
                    left_pad = 0
                    right_pad = 0
                tmp_image_name = self.uncrop(tmp_image_name,left_pad,right_pad,top_pad,bottom_pad)
     
        else:
            # raise Exception("Error in replacing the background, response code: {}".format(response.status_code))
            # print(response.content)
            raise Exception("Error in replacing the background, response code: {}".format(response.status_code))
        return tmp_image_name
    
    def background_fill_photapi(self,image_path,backgoround_prompt):
        url = 'https://prodapi.phot.ai/external/api/v2/user_activity/background-generator'
        headers = {
            'x-api-key': self.phot_x_api_key,
            'Content-Type': 'application/json'
            }
        data = {
            'file_name': image_path,
            'input_image_link': "https://previews.dropbox.com/p/thumb/ACLGsnF3FugExi4LOVOmGw9oQGS8gARXTqz1dqPYvqzyi47nwo0jD4d1qy04z2ghEX3dtKm8-V-eq8MPfg2Opamxo7y3-oz-GRYZEl4m5BnU5eb62yNxbKZnWtodrTMlDnFtRsi0ZAcHdCRFrLgNZ-BdGtCNzcZOup-YFfaG4Gfe_8vpczZuQek6ilX6sBij0yFS5eg1FR9nQ0L3CYvoyDmVCiCvcU_3BZdArXyg4eTprOBbdHn3Xe2I7f_AaekHRhxrGSVsj3__4zVX1t9AS12OHaTZNKJXixKehdhRsGDhFgbovwkv45yMyNYE2njVj-N3se2e8wMALBdv3ukVWf4B/p.jpeg",
            'prompt': backgoround_prompt
            }
        tmp_image_name = 'updated_background_image.jpg'
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            with open(tmp_image_name, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception("Error in replacing the background, response code: {}".format(response.status_code))

        return tmp_image_name
                

    # to fill the overlaid text
    def text_fill(self,image_path,output_image_name):
        if output_image_name:
            tmp_image_name = output_image_name
        else:
            tmp_image_name = 'updated_text_image.jpg'
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(self.font, size=100)
        text = self.overlaid_text
        text_size = draw.textsize(text, font=font)
        x = image.width - text_size[0] - 10
        y = image.height - text_size[1] - 10
        draw.text((x, y), text, font=font, fill=(255, 255, 0))
        image.save(tmp_image_name)
        return tmp_image_name


    # to genarate the thumbnail using all the functioanlities
    def genarate(self,output_image_name):
        try:
            tmp_image_name = self.image_path
            host = self.check_host(tmp_image_name)
            if not host:
                tmp_image_name = self.genarate_image(self.backgoround_prompt)
            else:
                if self.remove_background_flag:
                    tmp_image_name = self.remove_background(tmp_image_name)
                tmp_image_name = self.background_fill(tmp_image_name,"A plain white background")
            pixels, dimension = self.calculate_pixels_to_add(tmp_image_name)
            if pixels > 50:
                if self.expand_dim:
                    if self.expand_dim in ["right","left","top","bottom"]:
                        if dimension == "width":
                            if self.expand_dim == "right":
                                left_pad = 0
                                right_pad = pixels
                                top_pad = 0
                                bottom_pad = 0
                            else:
                                right_pad = 0
                                left_pad = pixels
                                top_pad = 0
                                bottom_pad = 0
                        else:
                            if self.expand_dim == "top":
                                top_pad = pixels
                                bottom_pad = 0
                                left_pad = 0
                                right_pad = 0
                            else:
                                bottom_pad = pixels
                                top_pad = 0
                                left_pad = 0
                                right_pad = 0
                    else:
                        raise ValueError("Invalid value for expand_dim, it should be one of ['right','left','top','bottom']")
                else:
                    if dimension == "width":
                        left_pad = pixels // 2
                        right_pad = pixels - left_pad
                        top_pad = 0
                        bottom_pad = 0
                    else:
                        top_pad = pixels // 2
                        bottom_pad = pixels - top_pad
                        left_pad = 0
                        right_pad = 0
                # tmp_image_name = self.uncrop(tmp_image_name,left_pad,right_pad,top_pad,bottom_pad)
                tmp_image_name = self.add_white_pixels_to_image(tmp_image_name, left_pad, right_pad, top_pad, bottom_pad)
                tmp_image_name = self.background_fill(tmp_image_name,"plain full white background")
                tmp_image_name = self.background_fill(tmp_image_name,self.backgoround_prompt)
            if host:
                tmp_image_name = self.background_fill(tmp_image_name,self.backgoround_prompt)
            tmp_image_name = self.text_fill(tmp_image_name,output_image_name)
            return "Your thumbnail is Successfully Genarated and Saved as {}".format(tmp_image_name)
        except Exception as e:
            return "{}".format(e)
    


if __name__ == "__main__":
    image_path = 'background.jpg'
    backgoround_prompt = 'A red ferrari on the background'
    text_prompt = 'a beautiful text'
    font = 'Sobread.ttf'
    overlaid_text = """Lamborghini
              Vs
      Ferrari  """
    remove_background_flag = False
    expand_dim = "right"

    n_samples = 3

    for i in range(n_samples):
        output_image_name = 'output' + str(i) + '.jpg'
        thumbnail_genartor = ThumbnailGenarator(image_path, backgoround_prompt, text_prompt, font, overlaid_text, remove_background_flag,expand_dim)
        print(thumbnail_genartor.genarate(f"output{i}.jpg"))
