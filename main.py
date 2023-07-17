#
# main.py
#
# The main file for the trimmer application
#

import tkinter as tk
import gui
import discord
import atexit

# create discord presence
discordPresence = None
def tryAddPresence(app):
    try:
        global discordPresence
        presence = discord.DiscordPresence()



        

        if str(app.getSceneType()) == str(gui.Scene.SCENE_INITIAL):
            presence.createPresence(details="Choosing videos")
        elif str(app.getSceneType()) == str(gui.Scene.SCENE_CLIPS):
            presence.createPresence(details="Clipping videos", state=f"{min(app.scene.currentVideo, app.scene.totalVideos)} of {app.scene.totalVideos}")
        elif str(app.getSceneType()) == str(gui.Scene.SCENE_TRIM):
            presence.createPresence(details="Trimming videos")

        


        presence.scheduleUpdates()   
        discordPresence = presence
        app.updateDiscordPresence(discordPresence)
    except Exception as e:
        # discord error / not open
        pass




if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x100")
    root.title("Bulk Video Trimmer")
    root.resizable(width=False, height=False)
    root.iconbitmap(gui.getResourcePath("images/logo.ico"))

    app = gui.MainApp(root)
    app.setScene(gui.Scene.SCENE_INITIAL)
    app.pack(fill="both", expand=True)

    root.after(15000, lambda: tryAddPresence(app))

    root.mainloop()


