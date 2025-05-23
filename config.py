import yaml
from constants import GROQ_API_KEY
import datetime


class AppConfig:
    def __init__(self):
        with open('settings.yaml', 'r') as f:
            self.settings = yaml.safe_load(f)

        self.LLM_MODEL = self.settings['llm']['model']
        self.CALLER_PA_PROMPT = self.settings['prompts']['caller_pa']

    def get_current_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")