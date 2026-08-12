from app.exceptions.base_exception import ApplicationException


class PredictionAlreadyExistsException(ApplicationException):

    def __init__(self) -> None:
        super().__init__(
            error_code="PREDICTION_ALREADY_EXISTS",
            message="Prediction already exists for this team and match",
            status_code=409,
        )


class ActualResultAlreadyExistsException(ApplicationException):

    def __init__(self) -> None:
        super().__init__(
            error_code="ACTUAL_RESULT_ALREADY_EXISTS",
            message="Actual result already exists for this match",
            status_code=409,
        )


class ResourceNotFoundException(ApplicationException):

    def __init__(self, resource_type: str = "Resource") -> None:
        super().__init__(
            error_code="RESOURCE_NOT_FOUND",
            message=f"{resource_type} not found",
            status_code=404,
            details={"resource_type": resource_type},
        )


class InvalidCompetitionStateException(ApplicationException):

    def __init__(self, message: str = "Invalid competition state for this operation") -> None:
        super().__init__(
            error_code="INVALID_COMPETITION_STATE",
            message=message,
            status_code=400,
        )
