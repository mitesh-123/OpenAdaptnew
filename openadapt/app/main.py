from functools import partial
from subprocess import Popen
import base64
import os
from simpleaichat import AIChat
from rich.console import Console

from nicegui import app, ui

from openadapt import config, replay
from openadapt.app.cards import recording_prompt, select_import, settings
from openadapt.app.objects.console import Console as AppConsole
from openadapt.app.util import clear_db, on_export, on_import

api_key = os.environ.get("SIMPLEAICHAT_API_KEY")
ai = AIChat(api_key=api_key, console=False, params={"temperature": 0.0})
console = Console(width=60, highlight=False)

tips = [
    "This ChatGPT model should answer every question."
]

tips_prompt = """From the list of topics below, reply ONLY with the number appropriate for describing the topic of the user's message. If none are, ONLY reply with "0".

1. Content after September 2021
2. Legal/Judicial Research
3. Medical/Psychatric Advice
4. Financial Advice
5. Illegal/Unethical Activies"""

params = {
    "temperature": 0.0,
    "max_tokens": 1,
    "logit_bias": {str(k): 100 for k in range(15, 15 + len(tips) + 1)}
}

# functional
ai.new_session(id="tips",
               api_key=api_key,
               system=tips_prompt,
               save_messages=False,
               params=params)

def check_user_input(message):
    tip_idx = ai(message, id="tips")
    if tip_idx == "0":
        return
    else:
        tip = tips[int(tip_idx) - 1]
        console.print(f"⚠️ {tip}", style="bold")

def chat_with_user():
    while True:
        user_input = input("[b]You:[/b] ").strip()
        if not user_input:
            break
        check_user_input(user_input)
        ai_response = ai(user_input)
        console.print(f"[b]ChatGPT[/b]: {ai_response}", style="bright_magenta")

SERVER = "127.0.0.1:8000/upload"
FPATH = os.path.dirname(__file__)

app.native.start_args["debug"] = False

dark = ui.dark_mode()
dark.value = config.APP_DARK_MODE

logger = None

def start(fullscreen: bool = False) -> None:
    """Start the OpenAdapt application."""
    with ui.row().classes("w-full justify-right"):
        with ui.avatar(color="white" if dark else "black", size=128):
            logo_base64 = base64.b64encode(
                open(os.path.join(FPATH, "assets/logo.png"), "rb").read()
            )
            img = bytes(
                f"data:image/png;base64,{(logo_base64.decode('utf-8'))}",
                encoding="utf-8",
            )
            ui.image(img.decode("utf-8"))
        ui.icon("settings").tooltip("Settings").on("click", lambda: settings(dark))
        ui.icon("delete").on("click", lambda: clear_db(log=logger)).tooltip(
            "Clear all recorded data"
        )
        ui.icon("upload").tooltip("Export Data").on("click", lambda: on_export(SERVER))
        ui.icon("download").tooltip("Import Data").on(
            "click", lambda: select_import(on_import)
        )
        ui.icon("share").tooltip("Share").on(
            "click", lambda: (_ for _ in ()).throw(Exception(NotImplementedError))
        )

        with ui.splitter(value=20) as splitter:
            splitter.classes("w-full h-full")
            with splitter.before:
                with ui.column().classes("w-full h-full"):
                    record_button = (
                        ui.icon("radio_button_checked", size="64px")
                        .on(
                            "click",
                            lambda: recording_prompt(["test"], record_button),
                        )
                        .tooltip("Record a new replay / Stop recording")
                    )
                    ui.icon("visibility", size="64px").on(
                        "click", partial(Popen, ["python", "-m", "openadapt.visualize"])
                    ).tooltip("Visualize the latest replay")

                    ui.icon("play_arrow", size="64px").on(
                        "click",
                        lambda: replay.replay("NaiveReplayStrategy"),
                    ).tooltip("Play the latest replay")
            with splitter.after:
                global logger
                logger = AppConsole()
                logger.log.style("height: 250px;, width: 300px;")

                # Add the chat console
                logger.log.clear()
                logger.log.style("height: 150px;, width: 300px;")
                logger.log.write("[b]ChatGPT[/b]: Ready for chat!", style="bright_magenta")

                # Start the chat
                chat_with_user()

            splitter.enabled = False

    ui.run(
        title="OpenAdapt Client",
        native=True,
        window_size=(400, 400),
        fullscreen=fullscreen,
        reload=False,
        show=False,
    )

if __name__ == "__main__":
    start()