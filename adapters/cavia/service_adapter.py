import networkx as nx  # type: ignore

from edge_sim_py.components.application import Application
from edge_sim_py.components.service import Service


class CaviaServiceAdapter:

    def __init__(self, graphml_path):
        self.graphml_path = graphml_path

    def load(self):

        G = nx.read_graphml(self.graphml_path)

        service_map = {}

        # creazione servizi
        for node_id, data in G.nodes(data=True):

            print(f"Processing node {node_id} with data: {data}")

            name = data.get("node_type", f"service_{node_id}")
            cpu_demand = int(data.get("0", 0))
            memory_demand = int(data.get("3", 0))
            processing_delay = int(data.get("4", 0))

            service = Service(node_id)

            service.name = name
            service.cpu_demand = cpu_demand
            service.memory_demand = memory_demand
            service.processing_delay = processing_delay

            service.step = int(data.get("step", 0))

            service_map[node_id] = service

        # creazione dipendenze
        for u, v, data in G.edges(data=True):

            print(f"Processing edge {u} -> {v} with data: {data}")

            data_size = int(data.get("3", 0))

            service_u = service_map[u]
            # service_v = service_map[v]

            # output size del servizio
            service_u.processing_output = data_size

        app = Application()

        ordered_services = sorted(service_map.values(), key=lambda s: s.step)

        for service in ordered_services:
            app.connect_to_service(service)

        return service_map, app


adapter = CaviaServiceAdapter("scenarios/cavia/1_26_solution_v0/ms/1MMM.graphml")

service_map, app = adapter.load()

print(service_map, len(service_map))
print(app.services, len(app.services))
