from edge_sim_py.utils.edge_sim_py_resetter import EdgeSimPyResetter
import pytest  # type: ignore

from edge_sim_py.components.application import Application
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.container_registry import ContainerRegistry
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.flow_scheduling import max_min_fairness
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
from edge_sim_py.components.user import User
from edge_sim_py.dataset_generator.edge_servers import jetson_tx2
from edge_sim_py.dataset_generator.map import hexagonal_grid
from edge_sim_py.dataset_generator.network_switches import sample_switch
from edge_sim_py.dataset_generator.network_topologies import partially_connected_fullduplex_hexagonal_mesh


class DummySchedule:
    def __init__(self):
        self.steps = 0
        self.agents = []

    def remove(self, agent):
        self.agents.remove(agent)


class DummyModel:
    def __init__(self):
        self.schedule = DummySchedule()
        self.topology = None
        self.network_flow_scheduling_algorithm = max_min_fairness

    def initialize_agent(self, agent):
        self.schedule.agents.append(agent)
        agent.model = self


def dummy_model():
    return DummyModel()


@pytest.fixture
def basic_topology():

    EdgeSimPyResetter.clear_all()

    # Creating the map coordinates
    map_coordinates = hexagonal_grid(x_size=3, y_size=3)

    # Creating the Base Stations and Network Switches
    # For every map coordinate 1 Base Station and 1 Network Switch
    for coordinates in map_coordinates:

        base_station = BaseStation()
        base_station.wireless_delay = 0
        base_station.coordinates = coordinates

        network_switch = sample_switch()
        base_station._connect_to_network_switch(network_switch=network_switch)

    # Creating Network Links and Topology
    topology = partially_connected_fullduplex_hexagonal_mesh(
        network_nodes=NetworkSwitch.all(),
        link_specifications=[
            {"number_of_objects": 16, "delay": 1, "bandwidth": 10},
        ],
    )

    return {
        "base_stations": BaseStation.all(),
        "network_switches": NetworkSwitch.all(),
        "topology": topology,
    }


@pytest.fixture
def small_app_2_user_4_services(basic_topology):
    """A small app with 2 user, 2 app and 4 services.

    data packet size = 20
    server n:4, processing time = 2+n, processing output = 10+n
    user position = (0,0) no mobility
    """
    # Creating the Edge Server
    servers = _servers_base_station(number_of_servers=4)

    # Creating the services
    services = _services_processing(number_of_services=4)

    # Assigning the services to the edge servers
    for server, service in zip(servers, services):
        server.services.append(service)
        service.server = server
        service._available = True

    # Creating users
    user1 = User()
    user1.set_packet_size_strategy(mode="fixed", size=20)
    user1._set_initial_position(coordinates=(0, 0))
    user1.mobility_model = _static_dummy_mobility

    user2 = User()
    user2.set_packet_size_strategy(mode="fixed", size=20)
    user2._set_initial_position(coordinates=(4, 0))
    user2.mobility_model = _static_dummy_mobility

    # Creating applications
    app1 = Application()
    ordered_services = sorted(services, key=lambda s: s.id)
    for service in ordered_services:
        app1.connect_to_service(service=service)

    app2 = Application()
    descending_services = sorted(services, key=lambda s: s.id, reverse=True)
    for service in descending_services:
        app2.connect_to_service(service=service)

    # Creating the model
    dummy_model = DummyModel()
    dummy_model.topology = basic_topology["topology"]

    basic_topology["topology"].model = dummy_model
    for app in [app1, app2]:
        app.model = dummy_model
    for user in [user1, user2]:
        user.model = dummy_model
    for service in services:
        service.model = dummy_model

    return {
        "user": [user1, user2],
        "application": [app1, app2],
        "services": ordered_services,
        "model": dummy_model,
    }


def _servers_base_station(number_of_servers: int):

    if len(BaseStation.all()) < number_of_servers:
        raise Exception("Not enough base stations")

    # Connecting the edge server to a random base station with no attached edge server
    base_stations = sorted(BaseStation.all(), key=lambda b: b.id)

    step = len(base_stations) / number_of_servers

    for i in range(number_of_servers):
        index = int(i * step + step / 2)
        base_station = base_stations[index]

        server = jetson_tx2()
        base_station._connect_to_edge_server(server)

    return EdgeServer.all()


def _services_processing(number_of_services: int):

    for i in range(number_of_services):

        Service(
            obj_id=i,
            cpu_demand=1,
            memory_demand=1200,
            state=0,
            processing_time=2 + i,
            processing_output=21 + i,
            image_digest="sha256:a777c9c66ba177ccfea23f2a216ff6721e78a662cd17019488c417135299cd89",
        )

    return Service.all()


def _static_dummy_mobility(user):
    user.coordinates_trace.append(user.coordinates)


def _dynamic_dummy_mobility(user):
    user.coordinates_trace.append((0, 0))


@pytest.fixture
def small_app_2_user_4_services_provision(basic_topology):
    """A small app with 2 user, 2 app and 4 services.
    No service assignment to edge servers.

    data packet size = 20
    server n:4, processing time = 2+n, processing output = 10+n
    requests start = 1, duration = 1, interval = 1
    user position = (0,0) no mobility
    """
    # Creating the Edge Server
    servers = _servers_base_station(number_of_servers=4)

    # Creating the services
    services = _services_processing(number_of_services=4)

    # Container image
    image1 = ContainerImage(
        obj_id=1,
        name="alpine",
        tag="",
        digest="sha256:a777c9c66ba177ccfea23f2a216ff6721e78a662cd17019488c417135299cd89",
        layers=["sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139"],
        architecture="",
    )

    image1.server = EdgeServer.all()[3]
    EdgeServer.all()[3].container_images.append(image1)

    # Container layer
    layer1 = ContainerLayer(
        obj_id=1, digest="sha256:df9b9388f04ad6279a7410b85cedfdcb2208c0a003da7ab5613af71079148139", size=2, instruction="ADD file:5d673d25da3a14ce1f6cf"
    )

    layer1.server = EdgeServer.all()[3]
    EdgeServer.all()[3].container_layers.append(layer1)

    # Container registry
    registry = ContainerRegistry(obj_id=1, cpu_demand=1, memory_demand=1024)

    registry.server = EdgeServer.all()[3]
    EdgeServer.all()[3].container_registries.append(registry)

    # Creating users
    user1 = User()
    user1.set_packet_size_strategy(mode="fixed", size=20)
    user1._set_initial_position(coordinates=(0, 0))
    user1.mobility_model = _static_dummy_mobility

    user2 = User()
    user2.set_packet_size_strategy(mode="fixed", size=20)
    user2._set_initial_position(coordinates=(4, 0))
    user2.mobility_model = _static_dummy_mobility

    # Creating applications
    app1 = Application()
    ordered_services = sorted(services, key=lambda s: s.id)
    for service in ordered_services:
        app1.connect_to_service(service=service)

    app2 = Application()
    descending_services = sorted(services, key=lambda s: s.id, reverse=True)
    for service in descending_services:
        app2.connect_to_service(service=service)

    # Creating the model
    dummy_model = DummyModel()
    dummy_model.topology = basic_topology["topology"]

    basic_topology["topology"].model = dummy_model
    for app in [app1, app2]:
        app.model = dummy_model
    for user in [user1, user2]:
        user.model = dummy_model
    for service in services:
        service.model = dummy_model
    for server in servers:
        server.model = dummy_model

    return {
        "user": [user1, user2],
        "application": [app1, app2],
        "services": ordered_services,
        "servers": servers,
        "model": dummy_model,
    }


def provisioning_algorithm():
    # First server with capacity to provision every service
    for service in Service.all():
        if service.server is None and not service.being_provisioned:

            for edge_server in EdgeServer.all():

                if edge_server.has_capacity_to_host(service=service):

                    service.provision(target_server=edge_server)

                    break
