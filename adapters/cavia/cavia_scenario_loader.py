import json
import os
import pickle
import networkx as nx  # type: ignore
import numpy as np

from adapters.cavia.utils.distributions import STRATEGY_REGISTRY
from edge_sim_py.components import User
from edge_sim_py.components.application import Application
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.network_link import NetworkLink
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.user_access_patterns.circular_duration_and_interval_access_pattern import CircularDurationAndIntervalAccessPattern
from edge_sim_py.dataset_generator.map.hexagonal_grid import hexagonal_grid
from edge_sim_py.utils.edge_sim_py_resetter import EdgeSimPyResetter


class CaviaScenarioLoader:
    def __init__(self, physical_graph_path, app_graph_path, pkl_path, seed=42, dist="deterministic"):
        self.physical_graph_path = physical_graph_path
        self.app_graph_path = app_graph_path
        self.pkl_path = pkl_path
        self.seed = seed

        if dist not in STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{dist}' non trovata nel registry. Strategie disponibili: {list(STRATEGY_REGISTRY.keys())}")
        self.strategy = STRATEGY_REGISTRY[dist]
        self.rng = np.random.default_rng(seed)

        with open(self.pkl_path, "rb") as f:
            self.data_pkl = pickle.load(f)

    def build_scenario(self):

        EdgeSimPyResetter.clear_all()

        # Load topology, basestations, switch, server
        topology, node_server_map = self._load_topology()

        # Load Services, Applications
        apps, service_map = self._load_services()

        # Placement with x_ui
        self._place_services(service_map, node_server_map)

        # Load Users
        users = self._build_users(apps)

        return topology, apps, users

    def _load_topology(self):
        G = nx.read_graphml(self.physical_graph_path)
        topology = Topology()
        node_switch_map = {}
        node_server_map = {}

        coords_list = hexagonal_grid(x_size=10, y_size=10)

        x_ui = self.data_pkl.get("x_ui", {})
        x_ui_filtered = {k: v for k, v in x_ui.items() if v > 0.5}

        nodes_used_by_solver = set()
        if x_ui_filtered:
            nodes_used_by_solver = {i for (u, i) in x_ui_filtered.keys()}

        for index, (node_id, data) in enumerate(G.nodes(data=True)):

            current_coords = coords_list[index] if index < len(coords_list) else (0, 0)

            # print(f"Processing node {node_id} with data: {data}")

            u_id = int(node_id)
            bs = BaseStation(u_id)
            switch = NetworkSwitch(u_id)

            bs.wireless_delay = 0
            bs.coordinates = current_coords
            bs._connect_to_network_switch(switch)
            node_switch_map[u_id] = switch
            topology.add_node(switch)

            cpu = int(data.get("0", 0))
            memory = int(data.get("1", 0))

            if cpu > 0 or memory > 0 or u_id in nodes_used_by_solver:

                server = EdgeServer(u_id)
                server.cpu = cpu
                server.memory = memory
                bs._connect_to_edge_server(server)
                node_server_map[u_id] = server

        for u, v, data in G.edges(data=True):
            # print(f"Processing edge {u} -> {v} with data: {data}")

            switch_u = node_switch_map[int(u)]
            switch_v = node_switch_map[int(v)]

            link = NetworkLink()
            link.topology = topology
            link.nodes = [switch_u, switch_v]
            link.delay = int(data.get("latency", 0))
            link.bandwidth = int(data.get("bandwidth", 0))

            topology.add_edge(switch_u, switch_v, object=link, delay=link.delay, bandwidth=link.bandwidth)
            switch_u.links.append(link)

        return topology, node_server_map

    def _load_services(self):
        G = nx.read_graphml(self.app_graph_path)

        if not self._is_graph_valid(G):
            self._log_invalid_scenario(self.app_graph_path)
            raise ValueError(f"Graph {self.app_graph_path} is invalid.")

        service_map = {}
        apps = []

        for node_id, data in G.nodes(data=True):

            u_id = int(node_id)
            service = Service(u_id)
            service.label = data.get("node_type", f"service_{u_id}")
            service.cpu_demand = int(data.get("0", 0))

            mean_val = float(data.get("4", 0))
            if mean_val <= 0:
                service.processing_time = 0
            else:
                service.processing_time = max(1, int(self.strategy(mean_val, self.rng)))

            service.processing_output = 1e-9

            service_map[u_id] = service

        input_node_ids = [n for n, d in G.nodes(data=True) if d.get("node_type") == "input"]
        dest_node_ids = [n for n, d in G.nodes(data=True) if d.get("node_type") == "destination"]

        for start_node in input_node_ids:

            target = dest_node_ids[0]
            paths = list(nx.all_simple_paths(G, source=start_node, target=target))

            for p in paths:
                app = Application()
                for node_id in p:
                    app.connect_to_service(service_map[int(node_id)])
                apps.append(app)

        return apps, service_map

    def _place_services(self, service_map, node_server_map):

        x_ui = self.data_pkl.get("x_ui", {})
        x_ui_filtered = {k: v for k, v in x_ui.items() if v > 0.5}

        for (id_servizio, id_nodo), _ in x_ui_filtered.items():

            server = node_server_map.get(id_nodo)
            service = service_map.get(id_servizio)

            if server and service:

                server.services.append(service)
                service.server = server

                server.cpu_demand += service.cpu_demand
                # server.memory_demand += service.memory_demand

                service._available = True

    def _build_users(self, apps):

        users = []

        for app in apps:
            user = User()
            user.set_packet_size_strategy(mode="fixed", size=1e-9)

            user._set_initial_position(app.services[0].server.coordinates)

            user.mobility_model = self.static_dummy_mobility
            user._connect_to_application(app=app, delay_sla=self.data_pkl.get("latency_limit", 0)[0])
            CircularDurationAndIntervalAccessPattern(user=user, app=app, start=1, duration_values=[1], interval_values=[501])

            users.append(user)

        return users

    def static_dummy_mobility(user):
        user.coordinates_trace.append(user.coordinates)

    def _is_graph_valid(self, G):
        if not nx.is_directed_acyclic_graph(G):
            return False
        if any(n for n, d in G.nodes(data=True) if d.get("node_type") != "input" and G.in_degree(n) == 0):
            return False
        return True

    def _log_invalid_scenario(self, app_graph_path):

        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "dump_scenarios", "invalid_scenarios.json")

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}

        parts = app_graph_path.split(os.sep)
        scenario = parts[-3] if len(parts) > 2 else "Unknown"
        app_name = os.path.splitext(os.path.basename(app_graph_path))[0]

        if scenario not in data:
            data[scenario] = []

        if app_name not in data[scenario]:
            data[scenario].append(app_name)

        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
