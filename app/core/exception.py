class PackageValidationError(Exception):
    """入力値が不正な場合の例外"""

    def __init__(self, message="入力値が不正です"):
        self.message = message
        super().__init__(f"{message}")
