# Real-Time-Co-Pilot
Realtime Transcriber Project
Introduction
The Realtime Transcriber is a Python-based application designed to provide live speech-to-text transcription using AssemblyAI's WebSocket API, with the ability to process and respond to the transcription in real-time using OpenAI's GPT models. This tool is particularly useful for interviews, meetings, or any scenario where live transcription and interaction is required.
Features
1. Real-time audio to text transcription via AssemblyAI.
2. Integration with OpenAI's GPT models for intelligent response generation.
3. Customizable model selection for different versions of GPT.
4. Live toggling of transcription using keyboard inputs.
5. Simple and interactive command line interface.
Installation
To set up the Realtime Transcriber, follow these steps:
1. Clone the repository to your local machine.
2. Install the required dependencies by running 'pip install -r requirements.txt' in your virtual environment.
3. Enter your AssemblyAI and OpenAI API keys in the 'configure.py' file.
Usage
To start the Realtime Transcriber, execute the 'main.py' script from the command line. The application will listen for the spacebar key to start or pause the transcription, and the escape key to exit the application.
Configuration
The 'configure.py' file contains several placeholders for API keys and user information. Replace the placeholder strings with your actual AssemblyAI and OpenAI API keys, your name, and the name of the interviewer or conversation partner.
Contributing
Contributions to the Realtime Transcriber project are welcome. To contribute, please fork the repository, make your changes, and submit a pull request.
License
The Realtime Transcriber is released under the MIT License. See the LICENSE file in the repository for full details.