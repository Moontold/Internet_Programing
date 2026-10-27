class AppError(Exception):
    """Бизнес-ошибка с понятным пользователю текстом на русском.

    Общий обработчик в app.main превращает её в конверт {error: true, message}.
    Обычно ответ идёт с HTTP 200; status_code задаётся там, где ответ — не JSON,
    а файл по прямой ссылке: браузеру нужен честный код 403 или 404.
    """

    def __init__(self, message: str, status_code: int = 200) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
