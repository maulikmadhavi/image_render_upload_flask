from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
import torch
import decord
from decord import VideoReader
from decord import cpu, gpu
from tqdm import tqdm
from groq import Groq
import ollama
  
class Florence2:
    def __init__(self) -> None:
        print("***************** Florence2 initialized ******************" )
        model_id = 'microsoft/Florence-2-large'
        self.model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, device_map="cuda:0").eval().cuda().half()
        self.processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        print("***************** Florence2 initialized ******************" )

    def get_info(self, file_path):
        image = Image.open(file_path)
        width, height = image.size
        return width, height
    
    def run_cap(self, img):
        return self.run_example("<MORE_DETAILED_CAPTION>", img)["<MORE_DETAILED_CAPTION>"]

    def run_example(self, task_prompt, image, text_input=None):
        if text_input is None:
            prompt = task_prompt
        else:
            prompt = task_prompt + text_input
        inputs = self.processor(text=prompt, images=image, return_tensors="pt").to('cuda', torch.float16)
        generated_ids = self.model.generate(
        input_ids=inputs["input_ids"].cuda(),
        pixel_values=inputs["pixel_values"].cuda(),
        max_new_tokens=1024,
        early_stopping=False,
        do_sample=False,
        num_beams=3,
        )
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = self.processor.post_process_generation(
            generated_text,
            task=task_prompt,
            image_size=(image.width, image.height)
            )

        return parsed_answer



class VideoProcessor:
    def __init__(self) -> None:
        self.captioner = Florence2()
    
    def get_caption(self, filename, time_step=1, wrap_time_str=True):
        self.vr = decord.VideoReader(filename)
        vr = VideoReader(filename, ctx=cpu(0))
        print('video frames:', len(vr))

        fps = round(vr.get_avg_fps())
        caption_dict = {}
        for i in tqdm(range(fps//2, len(self.vr), time_step*fps), desc='Processing frames', total=len(self.vr)//fps):
            img = Image.fromarray((self.vr[i].asnumpy()))
            # img.save(f'frame_{i}.png')
            caption = self.captioner.run_cap(img)
            caption_dict[i] = caption
            print(caption)
        
        time_caption_str = ""
        if wrap_time_str:
            time_caption_str = "\n".join([f"{k//fps}-{(k+time_step)//fps} sec: {v}" for k, v in caption_dict.items()])
        else:
            time_caption_str = "\n".join([f"{k}: {v}" for k, v in caption_dict.items()])
        return caption_dict, time_caption_str
class Model:
    def __init__(self) -> None:        
        print("***************** Model initialized ******************" )

    def get_info(self, file_path):
        image = Image.open(file_path)
        width, height = image.size
        return width, height


class LLM:
    def __init__(self) -> None:
        
        self.client = Groq()
    
    def run(self, num_frames: str, caption: str):
        prompt = f"""
        The following is a series of detailed image captions describing the content of a video frame by frame. The frames range from 0 seconds to {num_frames} seconds, with each frame depicting various scenes involving digital illustrations, computer screens, handwritten notes, and on-screen text. Your task is to generate a comprehensive summary of the video that captures the main themes and key events, without listing every individual frame description. Focus on providing an overview of the major changes or activities depicted in the frames and any recurring elements.

        Here is the list of image descriptions:
        {caption}
        """
        
        
        print("********************** ")
        
        print(prompt)
        print("****************")
        completion = self.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.01,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        return str(completion.choices[0].message.content)

class LLMOllama:
    def __init__(self) -> None:
        self.client = ollama.Client()
    
    def run(self, num_frames: str, caption: str):
        prompt = f"""
        The following is a series of detailed image captions describing the content of a video frame by frame. The frames range from 0 seconds to {num_frames} seconds, with each frame depicting various scenes involving digital illustrations, computer screens, handwritten notes, and on-screen text. Your task is to generate a comprehensive summary of the video that captures the main themes and key events, without listing every individual frame description. Focus on providing an overview of the major changes or activities depicted in the frames and any recurring elements.

        Here is the list of image descriptions:
        {caption}
        """
        
        print("********************** ")
        print(prompt)
        print("****************")
        
        response = self.client.chat(model='mistral:latest', messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ])
        
        return response['message']['content']


# class OllamaLLM:
#     def __init__(self) -> None:
        
    
#     You are given a list of captions that describe a series of images taken from a video, with each caption corresponding to a specific frame (from 0 seconds to 27 seconds). The images show various activities, including scenes of digital illustrations, computer screens, handwritten notes, and on-screen text.

#     Your task is to create a brief but comprehensive summary that captures the key events, themes, and transitions in the video. Follow these instructions:

#     Identify Major Themes: Focus on the main activities and recurring elements in the video, such as the digital illustrations, tasks displayed on the computer screen, and any writing on paper.
#     Summarize Significant Changes: Highlight the major shifts in content over time (e.g., from blank screens to text appearing, or from handwritten notes to digital illustrations).
#     Avoid Repetition: Combine similar events or themes across consecutive frames to avoid mentioning the same details repeatedly. For example, group frames that show writing on paper or similar text on the computer screen.
#     Convey the Flow: Describe the sequence of events in a way that gives a clear sense of how the video progresses over time.

#     Here is the list of captions for reference:

#     (0-1 sec): Screenshots showing a blank lined paper on a computer screen with editing icons.
#     (2-3 sec): A hand writing on a lined paper.
#     (4-11 sec): Displaying text like "Retype Scanned/PDF Files" and tasks such as handling emails and research, with a digital character wearing a suit.
#     (13-18 sec): Digital illustrations of a person, a lightbulb labeled "DJ," and text related to social media management.
#     (19-21 sec): Graphics of charts, graphs, and animal illustrations with business-related text.
#     (22-27 sec): Returns to lined paper with writing and mentions of PDF documents.

# Generate a summary that combines these details into a coherent description of the video content, focusing on the major changes and recurring themes.



if __name__ == "__main__":
    vp = VideoProcessor('/home/maulik/Documents/Tool/Coding_practice/flask_image_summarizer/static/renames/2024-10-14_00-33-55.mp4')
    vp.get_caption()
