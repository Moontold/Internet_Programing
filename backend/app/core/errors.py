class AppError(Exception):
    """Бизнес-ошибка с понятным пользователю текстом на русском.

    Общий обработчик в app.main превращает её в конверт {error: true, message}.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
