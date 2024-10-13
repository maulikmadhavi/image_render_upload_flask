from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
import torch
import decord
from decord import VideoReader
from decord import cpu, gpu
from tqdm import tqdm
from groq import Groq

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
        breakpoint()
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
        breakpoint()
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




if __name__ == "__main__":
    vp = VideoProcessor('/home/maulik/Documents/Tool/Coding_practice/flask_image_summarizer/static/renames/2024-10-14_00-33-55.mp4')
    vp.get_caption()
