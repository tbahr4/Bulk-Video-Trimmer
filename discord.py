#
# discord.py
#
# Creates a rich presence for discord
#

from pypresence import Presence
import time
import threading



class DiscordPresence():
    def __init__(self):
        self.clientID = "1125950120479948851"
        self.RPC = Presence(self.clientID)
        self.lastUpdate = 0
        self.start = int(time.time())

        # presence details
        self.details = None
        self.state = None
        self.displayedDetails = None
        self.displayedState = None

    def createPresence(self, details:str = None, state:str = None):
        """
            Initialize the presence and displays an initial state
        """
        self.RPC.connect()

        self.RPC.update(
            details=details or self.details, 
            state=state or self.state, 
            large_image="logo",
            start=self.start
        )

        self.details = details
        self.state = state
        self.lastUpdate = time.time()
        self.displayedDetails = self.details
        self.displayedState = self.state
        
    def updateStatus(self, details:str = None, state:str = None):
        """
            Updates the values for when the presence is next updated
        """
        self.details = None
        self.state = None
        if details != None: self.details = details
        if state != None: self.state = state

    def scheduleUpdates(self):
        """
            Starts automatic updates on a separate thread
        """
        updater = threading.Thread(target=self._update, daemon=True)
        updater.start()
    
    def _update(self):
        """
            Should only be run every 15 seconds
        """
        def update(results):
            try:
                self.RPC.update(
                    details=self.details,
                    state=self.state,
                    large_image="logo",
                    start=self.start
                )
                results["return"] = True
            except:
                results["return"] = False

        results = dict()
        thread = threading.Thread(target=update, args=(results,))        # avoids freeze
        thread.start()

        self.lastUpdate = time.time()

        # schedule next update
        for i in range(15):
            time.sleep(1)
        thread.join()       # should never still be alive
        
        if results["return"]:    
            self._update()


    def _TODO_REMOVE_sendUpdate(self):
        """
            Schedules an update to the presence to the given values
            Does not execute if it has not been 15 seconds since last update
            Does not execute if update is the same as the previous state
        """
        if not self.isUpdateNeeded: return

        timeSinceLastUpdate = time.time() - self.lastUpdate
        if timeSinceLastUpdate >= 15:
            self.RPC.update(
                details=self.details,
                state=self.state,
                large_image="logo",
                start=self.start
            )
            self.lastUpdate = time.time()

    def isUpdateNeeded(self):
        """
            Returns true if the current presence is different from the stored status
        """
        return self.details != self.displayedDetails or self.state != self.displayedState
            


    