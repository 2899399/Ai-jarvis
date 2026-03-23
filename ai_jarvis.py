#!/usr/bin/env python3
# ============================================================
#   AI JARVIS - Personal Hindi AI Assistant
#   Powered by: Ollama (Local AI - No API needed)
#   Author  : [Your Name]
#   Version : 1.0
# ============================================================
#
#   REQUIREMENTS:
#   pip install requests pyttsx3 speechrecognition pyaudio
#
#   USAGE:
#   python ai_jarvis.py
#
# ============================================================

import os
import sys
import json
import datetime
import webbrowser
import subprocess
import requests
import random

try:
    import pyttsx3
    TTS_OK = True
except ImportError:
    TTS_OK = False

try:
    import speech_recognition as sr
    VOICE_OK = True
except ImportError:
    VOICE_OK = False

# ── Colors ───────────────────────────────────────────────────
RED     = "\033[91m"
YELLOW  = "\033[93m"
GREEN   = "\033[92m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

# ── Banner ───────────────────────────────────────────────────
BANNER = f"""
{CYAN}{BOLD}
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
{RESET}
{DIM}   Aapka Personal Hindi AI Assistant
   Powered by LLaMA3 — 100% Local & Private{RESET}
{CYAN}{'─'*50}{RESET}
"""

# ── Ollama Settings ──────────────────────────────────────────
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3"

# ── JARVIS System Prompt (Hindi) ─────────────────────────────
SYSTEM_PROMPT = """
Aap JARVIS hain — ek smart, helpful aur friendly personal AI assistant.

Aapke baare mein:
- Aapka naam JARVIS hai
- Aap hamesha Hindi mein baat karte hain
- Aap bahut helpful, polite aur friendly hain
- Aap chhoti chhoti baaton mein bhi madad karte hain
- Aap user ko "Huzoor" ya "Boss" kehte hain (kabhi kabhi)

Aap yeh kaam kar sakte hain:
- Kisi bhi sawaal ka jawab dena
- Apps aur websites kholne mein madad karna
- System ki information batana
- Mausam, time, date batana
- Jokes sunana
- General conversation karna
- Cybersecurity ke baare mein batana

Important rules:
- Hamesha Hindi mein jawab dena
- Short aur clear jawab dena
- Agar koi app ya website kholni ho toh [ACTION: OPEN_APP: app_name] ya [ACTION: OPEN_URL: url] format use karna
- Agar web search karni ho toh [ACTION: SEARCH: query] format use karna
- Friendly aur helpful rehna
"""

# ── Conversation History ─────────────────────────────────────
conversation_history = []


# ════════════════════════════════════════════════════════════
#   VOICE ENGINE
# ════════════════════════════════════════════════════════════

def init_voice():
    if not TTS_OK:
        return None
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.setProperty("volume", 1.0)
        return engine
    except Exception:
        return None


def speak(engine, text):
    # Remove action tags before speaking
    clean = text
    for tag in ["[ACTION:", "]"]:
        clean = clean.replace(tag, "")
    print(f"\n  {CYAN}{BOLD}🤖 JARVIS:{RESET} {CYAN}{clean}{RESET}\n")
    if engine:
        try:
            engine.say(clean)
            engine.runAndWait()
        except Exception:
            pass


def listen(recognizer, mic):
    print(f"  {YELLOW}🎤 Bol rahe hain... sun raha hoon...{RESET}")
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        command = recognizer.recognize_google(audio, language="hi-IN")
        print(f"  {GREEN}✅ Aapne kaha: {command}{RESET}")
        return command
    except sr.WaitTimeoutError:
        print(f"  {YELLOW}⏱️  Kuch nahi suna...{RESET}")
        return ""
    except sr.UnknownValueError:
        print(f"  {YELLOW}❓ Samajh nahi aaya, dobara bolein.{RESET}")
        return ""
    except Exception as e:
        print(f"  {RED}[-] Voice error: {e}{RESET}")
        return ""


# ════════════════════════════════════════════════════════════
#   OLLAMA AI
# ════════════════════════════════════════════════════════════

def ask_jarvis(user_message):
    """Send message to local Ollama AI and get response."""
    global conversation_history

    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    payload = {
        "model"   : OLLAMA_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
        "stream"  : False
    }

    try:
        print(f"  {DIM}Soch raha hoon...{RESET}")
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data    = response.json()
        reply   = data["message"]["content"].strip()

        # Add assistant reply to history
        conversation_history.append({
            "role"   : "assistant",
            "content": reply
        })

        # Keep history manageable (last 10 messages)
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        return reply

    except requests.exceptions.ConnectionError:
        return "Ollama se connect nahi ho pa raha. Kripya Ollama start karein."
    except Exception as e:
        return f"Kuch gadbad ho gayi: {str(e)}"


# ════════════════════════════════════════════════════════════
#   ACTION HANDLER
# ════════════════════════════════════════════════════════════

def handle_actions(response, engine):
    """Parse and execute actions from AI response."""

    # Open App
    if "[ACTION: OPEN_APP:" in response:
        try:
            app = response.split("[ACTION: OPEN_APP:")[1].split("]")[0].strip()
            app_map = {
                "chrome"       : "chrome",
                "firefox"      : "firefox",
                "notepad"      : "notepad",
                "calculator"   : "calc",
                "vs code"      : "code",
                "paint"        : "mspaint",
                "file explorer": "explorer",
                "task manager" : "taskmgr",
                "spotify"      : "spotify",
                "discord"      : "discord",
                "whatsapp"     : "whatsapp",
                "word"         : "winword",
                "excel"        : "excel",
            }
            cmd = app_map.get(app.lower(), app)
            subprocess.Popen(cmd, shell=True)
            print(f"  {GREEN}✅ {app} khola gaya!{RESET}")
        except Exception as e:
            print(f"  {RED}[-] App nahi khuli: {e}{RESET}")

    # Open URL
    if "[ACTION: OPEN_URL:" in response:
        try:
            url = response.split("[ACTION: OPEN_URL:")[1].split("]")[0].strip()
            webbrowser.open(url)
            print(f"  {GREEN}✅ Website kholi gayi: {url}{RESET}")
        except Exception as e:
            print(f"  {RED}[-] Website nahi khuli: {e}{RESET}")

    # Web Search
    if "[ACTION: SEARCH:" in response:
        try:
            query = response.split("[ACTION: SEARCH:")[1].split("]")[0].strip()
            webbrowser.open(f"https://www.google.com/search?q={query}")
            print(f"  {GREEN}✅ Search kiya: {query}{RESET}")
        except Exception as e:
            print(f"  {RED}[-] Search nahi ho paya: {e}{RESET}")


# ════════════════════════════════════════════════════════════
#   DIRECT COMMANDS (Fast response without AI)
# ════════════════════════════════════════════════════════════

def handle_direct(command, engine):
    """Handle simple commands directly without AI."""
    cmd = command.lower().strip()

    # Time
    if any(w in cmd for w in ["time", "samay", "waqt", "baje"]):
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(engine, f"Huzoor, abhi {now} baj rahe hain.")
        return True

    # Date
    if any(w in cmd for w in ["date", "tareekh", "aaj", "din"]):
        today = datetime.datetime.now().strftime("%d %B %Y, %A")
        speak(engine, f"Huzoor, aaj {today} hai.")
        return True

    # Exit
    if any(w in cmd for w in ["exit", "quit", "bye", "band karo", "alvida", "band kr"]):
        speak(engine, "Alvida Huzoor! Apna khyal rakhein. 🙏")
        sys.exit(0)

    # Clear history
    if any(w in cmd for w in ["history clear", "bhool jao", "reset"]):
        global conversation_history
        conversation_history = []
        speak(engine, "Theek hai Huzoor, sab bhool gaya hoon!")
        return True

    # Switch to voice
    if any(w in cmd for w in ["voice mode", "awaaz se", "bolna hai"]):
        speak(engine, "Voice mode chalu kar raha hoon!")
        return "voice"

    # Switch to text
    if any(w in cmd for w in ["text mode", "likhna hai", "type"]):
        speak(engine, "Text mode chalu kar raha hoon!")
        return "text"

    return False


# ════════════════════════════════════════════════════════════
#   MAIN
# ════════════════════════════════════════════════════════════

def main():
    print(BANNER)

    # Check Ollama connection
    print(f"  {YELLOW}Ollama se connect ho raha hoon...{RESET}")
    try:
        r = requests.get("http://localhost:11434", timeout=3)
        print(f"  {GREEN}✅ Ollama connected!{RESET}")
    except Exception:
        print(f"  {RED}❌ Ollama nahi mila!")
        print(f"  CMD mein 'ollama serve' run karein phir dobara try karein.{RESET}")
        sys.exit(1)

    # Init voice
    engine = init_voice()

    # Init recognizer
    recognizer = None
    mic        = None
    if VOICE_OK:
        recognizer = sr.Recognizer()
        mic        = sr.Microphone()

    mode = "text"

    speak(engine, "Namaskar Huzoor! Main JARVIS hoon, aapka personal AI assistant. Aap mujhse kuch bhi pooch sakte hain!")
    print(f"  {DIM}Tip: 'voice mode' likhein awaaz se baat karne ke liye{RESET}")
    print(f"  {DIM}Tip: 'exit' likhein band karne ke liye{RESET}\n")

    while True:
        try:
            # Get input
            print(f"  {MAGENTA}[{mode.upper()} MODE]{RESET} ", end="")

            if mode == "voice" and VOICE_OK:
                command = listen(recognizer, mic)
                if not command:
                    continue
            else:
                command = input(f"{BOLD}Aap: {RESET}").strip()

            if not command:
                continue

            # Handle direct commands first (fast)
            result = handle_direct(command, engine)
            if result == "voice":
                mode = "voice"
                continue
            elif result == "text":
                mode = "text"
                continue
            elif result:
                continue

            # Send to AI
            response = ask_jarvis(command)

            # Handle any actions
            handle_actions(response, engine)

            # Speak response
            speak(engine, response)

        except KeyboardInterrupt:
            speak(engine, "Alvida Huzoor!")
            sys.exit(0)
        except Exception as e:
            print(f"  {RED}Error: {e}{RESET}")


if __name__ == "__main__":
    main()
