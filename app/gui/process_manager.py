class ProcessManager:
    def __init__(self):
        self.current_process = None

    def request_start(self, process_name):
        """
        Attempts to start a new process.
        :param process_name: Name of the process to start.
        :return: Tuple (success: bool, message: str)
        """
        if self.current_process is None:
            self.current_process = process_name
            return True, ""
        else:
            message = f"Process '{self.current_process}' is already running. Please stop it before starting a new one."
            return False, message

    def clear_process(self):
        """Clears the currently running process."""
        self.current_process = None

    def get_current_process(self):
        """Returns the name of the currently running process."""
        return self.current_process
