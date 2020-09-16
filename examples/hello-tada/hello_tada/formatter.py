
from colorama import init, Fore, Style
import emoji

init(autoreset=True)


def tada(text):
    text = Style.BRIGHT + Fore.MAGENTA + text
    text = text.replace("World", "Yaki")
    text = emoji.emojize(f":tada: {text} :tada:", use_aliases=True)
    return text
