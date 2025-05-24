# 🏥 Medora AI - Smart Medical Appointment System

## Why Do We Need Medora AI?

Modern healthcare and service industries face significant challenges in managing appointments efficiently. Traditional booking systems are often manual, time-consuming, and prone to errors or double-bookings. Patients and clients expect seamless, real-time interactions—preferably through natural language and voice—while providers need intelligent scheduling that adapts to their availability and priorities.

**Medora AI** addresses these needs by providing:
- **Frictionless, voice-first appointment booking** for patients and clients.
- **Intelligent, multi-agent orchestration** that optimizes scheduling, resolves conflicts, and adapts to urgency.
- **Automated notifications and reminders** to reduce no-shows and improve communication.
- **A scalable, extensible platform** ready for future AI advancements.

---

## 🌟 What Can Medora AI Do Right Now?

- **Conversational Booking:** Users can book, cancel, or check appointments using natural language—via chat or voice.
- **Voice Interaction:** Speak to the system and hear responses back, making the experience accessible and hands-free.
- **Multi-Agent Intelligence:** Three specialized AI agents (User Bot, Doctor Bot, Scheduler Bot) collaborate to understand user intent, recommend doctors, and manage scheduling.
- **Smart Scheduling:** The system checks doctor/provider availability, validates time slots, and prevents double-booking.
- **Conflict Resolution:** If a requested slot is unavailable, the system suggests alternatives in real time.
- **Priority Handling:** Urgent and emergency requests are prioritized using a Model Context Protocol (MCP).
- **Email Notifications:** Users receive booking confirmations, cancellations, and reminders automatically.
- **Dashboard & Manual Controls:** Staff can view, add, or cancel appointments directly from the dashboard.
- **Doctor Directory:** Users can browse available doctors, their specialties, and schedules.

---

## 🛠️ Technology Stack

- **Python 3.8+**
- **Streamlit:** For the interactive web UI.
- **LangChain & LangGraph:** For multi-agent orchestration and conversational AI.
- **Groq LLM:** For advanced language understanding and generation.
- **gTTS, pygame, SpeechRecognition:** For text-to-speech and speech-to-text capabilities.
- **smtplib, email:** For sending email notifications and reminders.
- **dotenv, yaml:** For configuration management.
- **Logging:** For robust monitoring and debugging.
- **pytz, numpy, sounddevice, vosk:** For time zone handling and audio processing.

---

## 🚀 Real-World Problems Solved

- **Manual Scheduling Hassles:** Eliminates the need for phone calls or manual entry by enabling conversational, automated booking.
- **Double-Booking & Conflicts:** Prevents scheduling errors by checking provider availability and resolving conflicts dynamically.
- **Missed Appointments:** Reduces no-shows with automated reminders and confirmations.
- **Accessibility:** Makes appointment management easier for users with disabilities or those who prefer voice interaction.
- **Urgency Management:** Ensures that urgent and emergency cases are prioritized appropriately.
- **Scalability:** Supports multiple providers and can be extended to other industries (consultants, salons, etc.).
- **Staff Efficiency:** Frees up administrative staff from repetitive scheduling tasks.

---

## 🔮 Future: Integrating the Agent Development Kit (ADK)

While Medora AI already leverages a robust multi-agent system, integrating an **Agent Development Kit (ADK)** in the future will unlock even greater capabilities:

- **Continuous Learning:** Agents can adapt to user preferences, learn from historical booking patterns, and personalize recommendations.
- **Custom Agent Creation:** Easily add new agents for specialized tasks (e.g., insurance verification, follow-up scheduling).
- **Plug-and-Play Upgrades:** Swap or upgrade agent logic without rewriting the core system.
- **Advanced Analytics:** Use ADK to analyze appointment trends, provider utilization, and user satisfaction.
- **Cross-Domain Expansion:** Extend the system to other domains (legal, education, wellness) by developing new agent modules.

---

## 🧑‍💻 Getting Started

### Prerequisites

- Python 3.8 or higher
- Streamlit
- Required Python packages (see `requirements.txt`)

### Installation

```bash
git clone https://github.com/yourusername/medora-ai.git
cd medora-ai
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
streamlit run app.py
```

---

## 📚 Usage

- **Book an Appointment:**  
  Start a conversation with "I would like to book an appointment" or use the voice input.
- **Check Availability:**  
  Ask "Show me available doctors" or "What are the next available appointments?"
- **Manage Appointments:**  
  View, cancel, or add appointments via the dashboard or chat.
- **Receive Notifications:**  
  Get email confirmations and reminders automatically.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with Streamlit
- Powered by Groq LLM
- Voice processing by PyAudio, gTTS, and SpeechRecognition
- Multi-agent architecture inspired by LangChain

---

## 📞 Support

For support, email support@medora-ai.com or open an issue in the repository.

---

Made with ❤️ by the Medora AI Team
```
