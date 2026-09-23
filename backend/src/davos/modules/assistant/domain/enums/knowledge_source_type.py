from enum import StrEnum


class KnowledgeSourceType(StrEnum):
    """Closed list of content kinds allowed in the public knowledge base.

    There is intentionally no member for customer data, tickets or internal notes, so such
    content cannot even be represented, let alone retrieved or sent to the model.
    """

    FAQ = "faq"
    POLICY = "policy"
    SERVICE = "service"
    PRICING = "pricing"
    CONTACT = "contact"
