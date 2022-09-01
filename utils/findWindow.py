import win32gui


def findWindow(title):
    return win32gui.FindWindow(None, title)


def changeWindow(id):
    win32gui.SetForegroundWindow(id)
