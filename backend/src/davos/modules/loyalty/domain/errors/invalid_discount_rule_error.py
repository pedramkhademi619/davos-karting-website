from davos.shared_kernel.domain.errors.validation_error import ValidationError


class InvalidDiscountRuleError(ValidationError):
    code = "invalid_discount_rule"
