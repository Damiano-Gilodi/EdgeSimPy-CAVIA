from adapters.cavia.cavia_scenario_loader import CaviaScenarioLoader
from adapters.cavia.find_valid_scenarios import get_scenario_paths
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.network_link import NetworkLink
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
from edge_sim_py.utils.edge_sim_py_resetter import EdgeSimPyResetter
import pytest  # type: ignore
import networkx as nx  # type: ignore


@pytest.fixture
def cavia_scenario():

    EdgeSimPyResetter.clear_all()

    scenario_name = "1_26_solution_v1"
    app_name = "1MMM"
    phys_path, app_path, pkl_path = get_scenario_paths(scenario_name, app_name)
    print("Loading scenario:", scenario_name)
    print("Loading app:", app_name + "\n")

    topology, apps, users = CaviaScenarioLoader(
        physical_graph_path=phys_path,
        app_graph_path=app_path,
        pkl_path=pkl_path,
        dist="exponential",
    ).build_scenario()

    G_topology = nx.read_graphml(phys_path)
    G_services = nx.read_graphml(app_path)

    return {
        "nodes_topology": G_topology.nodes(data=True),
        "edges_topology": G_topology.edges(data=True),
        "nodes_services": G_services.nodes(data=True),
        "links": NetworkLink.all(),
        "edge_servers": EdgeServer.all(),
        "switches": NetworkSwitch.all(),
        "base_stations": BaseStation.all(),
        "services": Service.all(),
        "app": apps[0],
        "user": users[0],
    }


def test_cavia_loader(cavia_scenario):

    assert len(cavia_scenario["base_stations"]) == len(cavia_scenario["switches"]) == len(cavia_scenario["nodes_topology"])

    assert len(cavia_scenario["links"]) == len(cavia_scenario["edges_topology"])

    for link in cavia_scenario["links"]:
        assert link.bandwidth >= 0
        assert link.delay >= 0
        assert len(link.nodes) >= 2

    for switch in cavia_scenario["switches"]:
        assert switch.base_station is not None
        assert switch.coordinates == switch.base_station.coordinates

    for server in cavia_scenario["edge_servers"]:
        assert server.cpu > 0
        assert server.memory > 0
        assert server.base_station is not None
        assert server.network_switch is not None
        assert server.coordinates == server.base_station.coordinates == server.network_switch.coordinates


def test_cavia_loader_services(cavia_scenario):

    assert len(cavia_scenario["services"]) == len(cavia_scenario["nodes_services"]) == len(cavia_scenario["app"].services)


def test_cavia_placement(cavia_scenario):

    for service in cavia_scenario["services"]:
        assert service.server is not None
        assert service.server.services is not None
        assert service in service.server.services
        assert service._available

    for server in cavia_scenario["edge_servers"]:
        if server.services:
            assert server.cpu_demand <= server.cpu

    total_placed_services = []
    for server in cavia_scenario["edge_servers"]:
        total_placed_services.extend(server.services)

    assert len(total_placed_services) == len(cavia_scenario["app"].services)

    for service in cavia_scenario["app"].services:
        assert total_placed_services.count(service) == 1


def test_cavia_loader_user(cavia_scenario):

    user = cavia_scenario["user"]
    app = cavia_scenario["app"]

    assert user.applications == [app]
    assert user.delay_slas[str(app.id)] > 0
    assert user.coordinates is not None
    assert user.base_station is not None
    assert user.base_station.coordinates == user.coordinates
    assert user.packet_size_strategy is not None
    assert user.packet_size_strategy["size"] == app.services[0].processing_output
    assert user.packet_size_strategy["mode"] == "fixed"
