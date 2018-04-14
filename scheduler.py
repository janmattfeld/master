#     Constraints during deployment planning:
#         - Service Dependencies -> Handled by the app itself
#         - Hard Constraints (Geo-Location, Technology, Resources, Features) -> Scheduler
#         - Soft Constraints (Availability, Performance, Price) -> Scheduler


def place(clouds, srv_template, sla):
    # Should SLAs only be considered at this level?
    # Combining several less reliable clouds might still be suitable?
    # TODO: Take a list of templates and optimize a whole app at once
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


# def place_service(clouds, service_template, sla):
#     req_instance_types = service_template.instances
#     req_regions = sla.regions
#     req_availability = sla.availability
#
#     offered_clouds = filter(lambda c: c.instance in req_instance_types, clouds)
#     offered_regions = filter(lambda c: c.location in req_regions, offered_clouds)
#     offered_availability = filter(lambda c: c.availability in req_availability, offered_regions)
#
#     offered_prices = sorted(offered_availability, key=lambda i: i['price'])
#
#     allocated_place = offered_prices[0]
#
#     if allocated_place is None:
#         raise SchedulerError("No match. Check cloud resources or change SLA.")
#     else:
#         return allocated_place
#
#
# # Pseudocode for Class App
# # Does not care about different services
# def scale(clouds, app_template, sla):
#     running_instances = filter_by_app(app_template, clouds)
#
#     is_replicated = len(running_instances) >= sla.replication_factor
#     is_overprovisioned = len(running_instances) >= sla.replication_factor + 1
#     meets_throughput = benchmark(app_template, sla) >= sla.throughput
#     idle_instances = filter(has_no_connection(i), running_instances)
#
#     if is_replicated and meets_throughput and is_overprovisioned:
#         most_expensive_idle = sorted(idle_instances, key=i['price'], reverse=True)
#         most_expensive_idle[0].shut_down()
#     elif not is_replicated or not meets_throughput:
#         place_service(clouds, service_template, sla)
