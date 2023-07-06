#
# main.py
#
# The main file for the trimmer application
#

import tkinter as tk
import gui
import discord

# create discord presence
discordPresence = discord.DiscordPresence()
discordPresence.createPresence()



if __name__ == "__main__":
    root = tk.Tk()
    root.title("Bulk Video Trimmer")
    root.resizable(width=False, height=False)
    root.iconbitmap(gui.getResourcePath("images/logo.ico"))

    app = gui.MainApp(root, discordPresence=discordPresence)
    app.setScene(gui.Scene.SCENE_INITIAL)
    app.pack(fill="both", expand=True)

    root.mainloop()
