class CullenError(Exception):
    pass


class CullenDecisionsError(CullenError):
    pass


class CullenDecisionsMissingError(CullenDecisionsError):
    pass


class FlopError(CullenError):
    pass
