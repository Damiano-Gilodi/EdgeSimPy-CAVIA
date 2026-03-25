import networkx as nx  # type: ignore

from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.network_link import NetworkLink
from edge_sim_py.components.topology import Topology


class CaviaTopologyAdapter:

    def __init__(self, graphml_path):
        self.graphml_path = graphml_path

    def load(self):

        # Load CAVIA physical graph
        G = nx.read_graphml(self.graphml_path)

        topology = Topology()

        node_map = {}

        # Creazione nodi switch
        for node_id, data in G.nodes(data=True):

            # print(f"Processing node {node_id} with data: {data}")

            cpu = int(data.get("0", 0))
            ram = int(data.get("1", 0))

            # Creazione Base Station
            bs = BaseStation(node_id)
            bs.wireless_delay = 0

            # Creazione switch
            switch = NetworkSwitch(node_id)
            node_map[node_id] = switch
            topology.add_node(switch)
            bs._connect_to_network_switch(switch)

            # Creazione Edge Server se ha risorse
            if cpu > 0 or ram > 0:
                server = EdgeServer(node_id)
                server.cpu = cpu
                server.memory = ram
                server.disk = 1000  # default se non indicato
                bs._connect_to_edge_server(server)

        # Creazione link tra switch
        for u, v, data in G.edges(data=True):

            # print(f"Processing edge {u} -> {v} with data: {data}")

            bandwidth = int(data.get("bandwidth", 0))
            latency = int(data.get("latency", 0))

            node_u = node_map[u]
            node_v = node_map[v]

            topology.add_edge(node_u, node_v)

            link = NetworkLink()
            link.topology = topology
            link.nodes = [node_u, node_v]
            link.delay = latency
            link.bandwidth = bandwidth

            topology._adj[node_u][node_v] = link
            node_u.links.append(link)

        return topology, node_map


adapter = CaviaTopologyAdapter("scenarios/cavia/1_26_solution_v0/physical_graph.graphml")

topology, node_map = adapter.load()

print("Nodes:", len(topology.nodes))
print("Links:", len(topology.edges))
# print("Node map:", node_map)
print(NetworkSwitch.all(), len(NetworkSwitch.all()))
print(EdgeServer.all(), len(EdgeServer.all()))
