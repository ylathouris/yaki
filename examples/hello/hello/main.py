import yaki


def hello():
    text = "Hello World!"
    formatters = yaki.load_plugins("hello.formatters")
    for formatter in formatters:
        text = formatter(text)

    print(text)
