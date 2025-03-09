from threading import Timer, Lock


class RepeatedTimer(object):
    """Class for creating a timer that executes a function repeatedly at specified intervals."""
    
    def __init__(self, interval, function, *args, **kwargs):
        """
        Initialize the timer with the interval and function to run.
        
        Args:
            interval (float): Time interval in seconds between function calls
            function (callable): Function to be called
            *args: Additional args for the function
            **kwargs: Additional kwargs for the function
        """
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self._lock = Lock()
        self.start()

    def _run(self):
        """Internal method to run the timer and execute the function."""
        with self._lock:
            self.is_running = False
            self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        """Start the timer if it's not already running."""
        with self._lock:
            if not self.is_running:
                self._timer = Timer(self.interval, self._run)
                self._timer.daemon = True  # Make timer daemon to exit with main thread
                self._timer.start()
                self.is_running = True

    def stop(self):
        """Stop the timer."""
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
                self.is_running = False
