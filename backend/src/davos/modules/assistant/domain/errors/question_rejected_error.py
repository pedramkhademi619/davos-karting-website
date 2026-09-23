from davos.shared_kernel.domain.errors.validation_error import ValidationError


class QuestionRejectedError(ValidationError):
    code = "question_rejected"
