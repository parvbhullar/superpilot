import pyttsx3
import requests
import speech_recognition as sr
import openai
import uuid
import gradio as gr
from threading import Thread
from vapi_python import Vapi  

class Vapi:
    def __init__(self, *, api_key, api_url="https://api.vapi.ai", openai_api_key=None):
        self.api_key = api_key
        self.api_url = api_url
        self.speaker = pyttsx3.init()
        if openai_api_key:
            openai.api_key = openai_api_key
        print("Vapi initialized with API key:", self.api_key)

    def speak_text(self, text):
        try:
            print(f"Speaking: {text}")
            self.speaker.say(text)
            self.speaker.runAndWait()
        except Exception as e:
            print(f"Error during TTS: {e}")

    def create_web_call(self, payload):
        try:
            print(f"Sending web call request with payload: {payload}")
            response = requests.post(
                f"{self.api_url}/call/web",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            response_data = response.json()
            print(f"Received response: {response_data}")

            call_id = response_data.get("id")
            web_call_url = response_data.get("webCallUrl")

            if not call_id or not web_call_url:
                print("Invalid API response: Missing call ID or web call URL.")
                return None, None

            return call_id, web_call_url
        except requests.exceptions.RequestException as e:
            print(f"Network error during web call creation: {e}")
            return None, None
        except ValueError:
            print("Error parsing JSON response from API.")
            return None, None

    def listen_for_conversation(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        with microphone as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening for speech...")

            while True:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    text = recognizer.recognize_google(audio)
                    print(f"User said: {text}")

                    if "stop" in text.lower():
                        print("Ending call.")
                        break

                    # Speak back the recognized text
                    self.speak_text(f"You said: {text}")
                except sr.WaitTimeoutError:
                    print("Listening timeout. Speak again.")
                except sr.UnknownValueError:
                    print("Could not understand the audio. Please try again.")
                except sr.RequestError as e:
                    print(f"Error with speech recognition service: {e}")

    def gradio_demo(self):
        def start_web_call(agent_id):
            try:
                uuid.UUID(agent_id)  # Validate UUID
                print(f"Initiating web call for agent ID: {agent_id}")
                payload = {"assistantId": agent_id}
                call_id, web_call_url = self.create_web_call(payload)
                
                if web_call_url:
                    print(f"Web call URL: {web_call_url}")
                    # Instead of joining in the terminal, return the URL
                    return f"Call successfully initiated. Join here: {web_call_url}"
                else:
                    return "Failed to initiate the call. Please check the logs."
            except Exception as e:
                print(f"Error during web call initiation: {e}")
                return f"Error: {e}"

        agents = [{"id": "51763287-d285-4220-8a77-a47d7743b4cf", "name": "Anchal-hindi"}]

        with gr.Blocks() as demo:
            gr.Markdown("## Web Call with Agent Selection")
            
            agent_dropdown = gr.Dropdown(
                choices=[agent["id"] for agent in agents],
                label="Select Agent",
                type="value"
            )
            
            start_call_button = gr.Button("Start Web Call")
            status_output = gr.Textbox(label="Call Status", interactive=False)

            start_call_button.click(fn=start_web_call, inputs=agent_dropdown, outputs=status_output)

        demo.launch(share=True)


if __name__ == "__main__":
    api_key = "8c3e405d-060c-4497-9ee5-67b5a62505ce"  # Ensure this is your actual API key
    vapi = Vapi(api_key=api_key)

    # Start the speech listening in a separate thread to prevent blocking the Gradio UI
    listen_thread = Thread(target=vapi.listen_for_conversation)
    listen_thread.daemon = True  # Ensures the thread will exit when the main program exits
    listen_thread.start()

    vapi.gradio_demo()  # Launch the Gradio UI
