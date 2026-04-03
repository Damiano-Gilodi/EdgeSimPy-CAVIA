from edge_sim_py.components.application import Application
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.container_registry import ContainerRegistry
from edge_sim_py.components.data_packet import DataPacket
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.network_link import NetworkLink
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.user import User
from edge_sim_py.components.user_access_patterns.circular_duration_and_interval_access_pattern import CircularDurationAndIntervalAccessPattern


class EdgeSimPyResetter:
    @staticmethod
    def clear_all():
        classes_to_reset = [
            Topology,
            NetworkLink,
            BaseStation,
            NetworkSwitch,
            EdgeServer,
            Service,
            User,
            Application,
            DataPacket,
            NetworkFlow,
            ContainerImage,
            ContainerLayer,
            ContainerRegistry,
            CircularDurationAndIntervalAccessPattern,
        ]
        for cls in classes_to_reset:
            if hasattr(cls, "_instances"):
                cls._instances = []
            if hasattr(cls, "_object_count"):
                cls._object_count = 0
