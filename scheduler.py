#     Constraints during deployment planning:
#         - Service Dependencies -> Handled by the app itself
#         - Hard Constraints (Geo-Location, Technology, Resources, Features) -> Scheduler
#         - Soft Constraints (Availability, Performance, Price) -> Scheduler


def place(clouds, srv_template, sla):
    # Should SLAs only be considered at this level?
    # Combining several less reliable clouds might still be suitable?

    # Currently returning the first cloud offering a supported provider.
    return list(filter(lambda c: c.provider in srv_template['provider'], clouds))[0]


def filter_provider(cloud, srv_template):
    """Remove non-supported clouds"""
    pass


def weight():
    """Find the most suitable cloud"""
    pass


def check(clouds, srv_template, sla):
    """Are the requirements still satisfied?"""
    pass
