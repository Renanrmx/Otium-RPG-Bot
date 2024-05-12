import os
from dotenv import load_dotenv
import google.generativeai as gemini


load_dotenv()
gemini.configure(api_key=os.getenv("GEMINI_TOKEN"))

generation_config = {
    "candidate_count": 1,
    "temperature": 1
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    },
]


class GeminiAssistant:

    model = gemini.GenerativeModel(model_name="gemini-1.0-pro",
                                  generation_config=generation_config,
                                  safety_settings=safety_settings)

    def send_prompt(self, prompt: str):
        convo = self.model.start_chat(history=[])
        convo.send_message(prompt)

        return convo.last.text
