import yaml
import os
from dotenv import load_dotenv
import datetime
from logger import setup_logger
from langchain_groq import ChatGroq

logger = setup_logger(__name__)

class AppConfig:
    def __init__(self):
        self._load_env_vars()
        self._load_settings()
        self._init_email_config()
        self._validate_config()
 
        self.llm_model_name = os.getenv("LLM_MODEL", self.settings['llm']['model'] if hasattr(self, 'settings') and 'llm' in self.settings else "gemma-7b")
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY", ""),
            model=self.llm_model_name,
            temperature=float(os.getenv("LLM_TEMPERATURE", self.settings['llm']['temperature'] if hasattr(self, 'settings') and 'llm' in self.settings else 0.7)),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", self.settings['llm']['max_tokens'] if hasattr(self, 'settings') and 'llm' in self.settings else 1000))
        )

    def _load_env_vars(self):
        """Load environment variables from .env file"""
        env_path = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_path):
            logger.info(".env file found")
            load_dotenv(env_path)
        else:
            logger.warning(".env file not found")

        
        self.groq_api_key = os.getenv('GROQ_API_KEY', '')
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.voice_enabled = os.getenv('VOICE_ENABLED', 'True').lower() == 'true'
        self.voice_language = os.getenv('VOICE_LANGUAGE', 'en-US')

    def _load_settings(self):
        """Load settings from YAML file with proper encoding"""
        try:
            with open('settings.yaml', 'r', encoding='utf-8') as f:
                self.settings = yaml.safe_load(f)
                
         
            self.llm_model = self.settings['llm']['model']
            self.llm_temperature = self.settings['llm']['temperature']
            self.llm_max_tokens = self.settings['llm']['max_tokens']
            self.prompts = self.settings['prompts']
            self.doctor_schedules = self.settings['doctor_schedules']
            
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            raise RuntimeError(f"Failed to load settings: {e}")

    def _init_email_config(self):
        """Initialize email configuration"""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        self.email_templates_dir = self.settings['email']['templates_dir']
        self.reminder_intervals = self.settings['email']['reminder_intervals']

    def _validate_config(self):
        """Validate the configuration"""
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
            
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email features will be disabled.")
        
        if not os.path.exists(self.email_templates_dir):
            os.makedirs(self.email_templates_dir)
            logger.info(f"Created email templates directory: {self.email_templates_dir}")

    def get_current_time(self):
        """Get current time in string format"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")