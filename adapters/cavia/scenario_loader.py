from adapters.cavia.service_adapter import CaviaServiceAdapter
from adapters.cavia.topology_adapter import CaviaTopologyAdapter


topology_adapter = CaviaTopologyAdapter("scenarios/cavia/.../physical_graph.graphml")

topology, node_map = topology_adapter.load()


service_adapter = CaviaServiceAdapter("scenarios/cavia/.../ms/1MMS.graphml")

services = service_adapter.load()
