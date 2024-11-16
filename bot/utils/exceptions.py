class RequestError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Error during request to external server")
