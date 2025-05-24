# 🏥 Medora AI - Smart Medical Appointment System

Medora AI is an intelligent medical appointment scheduling system powered by multi-agent AI technology. It combines the capabilities of three specialized AI agents to provide a seamless appointment booking experience.

## ✨ Features

- **🤖 Multi-Agent System**
  - User Bot: Handles initial interactions and intent recognition
  - Doctor Bot: Provides medical recommendations and doctor availability
  - Scheduler Bot: Manages appointment scheduling operations

- **📅 Appointment Management**
  - Book appointments with preferred doctors
  - View available time slots
  - Cancel appointments
  - Automatic confirmation system
  - Smart doctor recommendations based on medical needs

- **👨‍⚕️ Doctor Directory**
  - Comprehensive list of doctors with specialties
  - Real-time availability checking
  - Detailed doctor schedules and locations

- **🎤 Voice Interaction**
  - Voice command support
  - Text-to-speech responses
  - Natural language processing

- **📊 Dashboard Features**
  - Current appointments overview
  - Appointment statistics
  - System status monitoring
  - Manual booking interface

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Streamlit
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/medora-ai.git
cd medora-ai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
streamlit run app.py
```

## 🛠️ Configuration

The system can be configured through:
- `settings.yaml`: Main configuration file
- `.env`: Environment variables
- `config.py`: Application configuration class

### Environment Variables

```env
GROQ_API_KEY=your_groq_api_key
SMTP_HOST=your_smtp_host
SMTP_PORT=your_smtp_port
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
```

## 📚 Usage

### Booking an Appointment

1. Start a conversation with "I would like to book an appointment"
2. Choose from available time slots
3. Provide your name and preferred doctor
4. Confirm the booking details

### Checking Availability

- Use "Show me available doctors" to see the doctor directory
- Use "What are the next available appointments?" to check time slots

### Managing Appointments

- View current appointments in the dashboard
- Cancel appointments using the cancel button
- Receive email confirmations for bookings and cancellations

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Streamlit
- Powered by Groq LLM
- Voice processing by PyAudio
- Multi-agent architecture inspired by LangChain

## 📞 Support

For support, email support@medora-ai.com or open an issue in the repository.

---

Made with ❤️ by the Medora AI Team 