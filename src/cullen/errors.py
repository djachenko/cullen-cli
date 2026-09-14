class CullenError(Exception):
    pass


class DecisionsFileError(CullenError):
    pass


class DecisionsFileMissingError(DecisionsFileError):
    pass


class FlopError(CullenError):
    pass
