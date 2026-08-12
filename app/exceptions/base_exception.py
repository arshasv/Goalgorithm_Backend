class ApplicationException(Exception):

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        details: dict | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "success": False,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }
