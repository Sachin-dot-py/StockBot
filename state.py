class StateDB():
    """ Manage current state of user for continuity """
    
    def setState(self, state):
        with open("temp.txt", "w") as f:
            f.write(state + "\n")

    def getState(self):
        with open("temp.txt", "r") as f:
            state = f.read().splitlines()[0]
        return None if state == "None" else state

    def deleteState(self):
        with open("temp.txt", "w") as f:
            f.write("None")

    def addVar(self, var):
        with open("temp.txt", "a") as f:
            f.write(str(var) + "\n")

    def getVars(self):
        with open("temp.txt", "r") as f:
            temp_vars = [line for line in f.read().splitlines() if line]
        return temp_vars