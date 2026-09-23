from davos.shared_kernel.domain.errors.validation_error import ValidationError


class InvalidKnowledgeEntryError(ValidationError):
    code = "invalid_knowledge_entry"
