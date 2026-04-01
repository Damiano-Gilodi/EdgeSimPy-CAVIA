"""Contains data packet-related functionality."""

# EdgeSimPy components
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.service import Service

# Mesa modules
from mesa import Agent  # type: ignore[import]

if TYPE_CHECKING:
    from edge_sim_py.components.application import Application
    from edge_sim_py.components.user import User


@dataclass(frozen=True)
class LinkHop:
    """Class that represents a link hop in the data packet's path."""

    hop_index: int
    link_index: int

    source: int
    target: int

    start_time: int
    end_time: int

    queue_delay: int
    transmission_delay: int
    processing_delay: int
    propagation_delay: int

    min_bandwidth: float
    max_bandwidth: float
    avg_bandwidth: float

    data_input: int
    data_output: int


class DataPacket(ComponentManager, Agent):
    """Class that represents an data packet."""

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances: list["DataPacket"] = []
    _object_count = 0

    def __init__(self, user: "User", application: "Application", size: int = 1, obj_id: int | None = None):
        """Creates a DataPacket object.

        Args:
            user (User): User object.
            application (Application): Application object.
            size (int, optional): Size of the data packet in bytes.
            obj_id (int, optional): Object identifier.

        Returns:
            object: Created DataPacket object.
        """
        if size <= 0:
            raise ValueError("DataPacket size must be a positive integer.")

        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Data packet size change in services processing
        self.size = size

        # Application
        self.application: "Application" = application

        # User
        self.user: "User" = user

        # Status: active(default), finished, processing, dropped
        self._status = "active"

        # Total path (list of hop nodes between services)
        self._total_path: list[list[NetworkSwitch]] = []

        # Hops
        self._current_hop = 0
        self._current_link = 0

        # Processing
        self._is_processing = False
        self._processing_remaining_time = 0
        self._processing_output = 0
        self._processing_switch = None

        # Hops
        self._link_hops: list[LinkHop] = []

        # Current flow
        self._current_flow: "NetworkFlow | None" = None

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = None
        self.unique_id = None

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        return {
            "id": self.id,
            "user": self.user.id,
            "application": self.application.id,
            "size": self.size,
            "status": self._status,
            "current_hop": self._current_hop,
            "current_link": self._current_link,
            "is_processing": self._is_processing,
            "processing_remaining_time": self._processing_remaining_time,
            "total_path": [[sw.id for sw in hop] for hop in self._total_path],
            "hops": [asdict(hop) for hop in self._link_hops],
        }

    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """

        total_path = [[network_switch.id for network_switch in hop] for hop in self._total_path]

        return {
            "Id": self.id,
            "User": self.user.id,
            "Application": self.application.id,
            "Size": self.size,
            "Status": self._status,
            "Queue Delay": self.queue_delay_total,
            "Transmission Delay": self.transmission_delay_total,
            "Processing Delay": self.processing_delay_total,
            "Propagation Delay": self.propagation_delay_total,
            "Total Delay": self.total_delay,
            "Total Path": total_path,
            "Hops": [asdict(hop) for hop in self._link_hops],
        }

    def get_hops(self) -> list[LinkHop]:
        """Method that returns the data packet's hops.

        Returns:
            Data packet's hops.
        """
        return self._link_hops.copy()

    def step(self):
        """Method that executes the events involving the object at each time step."""

        # Processing
        if self._is_processing:

            service = self.application.services[self._current_hop - 1]

            if service.server is None or service.server.network_switch != self._processing_switch:
                self._status = "dropped"
                self._is_processing = False
                return

            self._processing_remaining_time -= 1
            if self._processing_remaining_time <= 0:
                self._is_processing = False
                self.size = self._processing_output
                if self._current_hop < len(self._total_path):
                    self._status = "active"
                    self._launch_next_flow(start_step=self.model.schedule.steps)
                else:
                    self._status = "finished"
            return

        # Launching the next flow
        if self._current_hop < len(self._total_path):
            if self._current_flow is None and self._status == "active":
                self._launch_next_flow(start_step=self.model.schedule.steps)
        else:
            self._status = "finished"

    def _launch_next_flow(self, start_step):
        """Method that lauches the next flow.

        Args:
            start_step (int): Time step in which the flow started.
        """
        hop = self._current_hop
        link = self._current_link

        if hop >= len(self._total_path):
            raise IndexError("Index hop out of range. No more services to process.")

        # If hop has only one node -> skip flow
        if len(self._total_path[hop]) == 1:
            self._handle_last_node(flow=None, hop=hop, link=link)
            return

        if link + 1 >= len(self._total_path[hop]):
            raise IndexError("Index link out of range.")

        flow = NetworkFlow(
            topology=self.application.model.topology,
            source=self._total_path[hop][link],
            target=self._total_path[hop][link + 1],
            path=self._total_path[hop][link : link + 2],
            start=start_step,
            data_to_transfer=self.size,
            metadata={"type": "data_packet", "object": self, "index_hop": hop, "index_link": link},
        )

        self._current_flow = flow
        self.model.initialize_agent(flow)

    def _on_flow_finished(self, flow: NetworkFlow):
        """Method that executes when a data packet flow finishes.

        Args:
            flow (NetworkFlow): Finished flow.
        """

        hop = flow.metadata["index_hop"]
        link = flow.metadata["index_link"]

        if hop >= len(self._total_path):
            raise IndexError("Index hop out of range. No more services to process.")

        if link + 1 >= len(self._total_path[hop]):
            raise IndexError("Index link out of range.")

        is_last_link = link + 1 == len(self._total_path[hop]) - 1

        # In intermediate link node
        if not is_last_link:

            self._handle_intermediate_node(flow, hop, link)
            return

        # In last link node hop
        self._handle_last_node(flow, hop, link)

    def _handle_intermediate_node(self, flow: NetworkFlow, hop: int, link: int):
        """Method that handles the intermediate node of a flow.

        Args:
            flow (NetworkFlow): Network flow.
            hop (int): Hop index.
            link (int): Link index.
        """
        self._add_link_hop(flow)

        self._current_hop = hop
        self._current_link = link + 1
        self._current_flow = None

    def _handle_last_node(self, flow: NetworkFlow | None, hop: int, link: int):
        """Method that handles the last node of a flow.
        If flow is None, it means that hop have only one node.

        Args:
            flow (NetworkFlow): Network flow.
            hop (int): Hop index.
            link (int): Link index.
        """
        service: "Service" = self.application.services[hop]

        if flow is None:
            switch: "NetworkSwitch" = self._total_path[hop][0]
        else:
            switch = self._total_path[hop][link + 1]

        target_server = service.server
        if target_server not in switch.edge_servers:
            self._status = "dropped"
            self._current_flow = None
            return

        self._add_link_hop(flow, service=service)
        service._start_processing(data_packet=self)

        self._processing_switch = switch
        self._status = "processing"
        self._current_hop = hop + 1
        self._current_link = 0
        self._current_flow = None

    def _add_link_hop(self, flow: NetworkFlow | None, service: "Service | None" = None):
        """Method that adds a link hop to the data packet.
        If no flow is provided, it adds the current hop.

        Args:
            flow (NetworkFlow): Network flow.
            service (Service, optional): Service associated with the flow. Defaults to None.
        """
        if flow is None:

            hop = self._current_hop
            link = 0

            if len(self._link_hops) == 0:
                start_time = self.model.schedule.steps
            else:
                start_time = self._link_hops[-1].end_time

            link_hop = LinkHop(
                hop_index=hop,
                link_index=link,
                source=self._total_path[hop][link].id,
                target=self._total_path[hop][link].id,
                start_time=start_time,
                end_time=start_time + (service.processing_time if service else 0),
                queue_delay=0,
                transmission_delay=0,
                processing_delay=service.processing_time if service else 0,
                propagation_delay=0,
                min_bandwidth=0,
                max_bandwidth=0,
                avg_bandwidth=0,
                data_input=self.size,
                data_output=service.processing_output if service else self.size,
            )

            self._link_hops.append(link_hop)
            return

        hop = flow.metadata["index_hop"]
        link = flow.metadata["index_link"]

        link_hop = LinkHop(
            hop_index=hop,
            link_index=link,
            source=flow.source.id,
            target=flow.target.id,
            start_time=flow.start,
            end_time=flow.end + (service.processing_time if service else 0),
            queue_delay=flow._queue_delay,
            transmission_delay=(flow.end - flow.start) - flow._queue_delay,
            processing_delay=service.processing_time if service else 0,
            propagation_delay=flow.topology[flow.path[0]][flow.path[1]]["delay"],
            min_bandwidth=min(flow._bandwidth_history),
            max_bandwidth=max(flow._bandwidth_history),
            avg_bandwidth=sum(flow._bandwidth_history) / len(flow._bandwidth_history),
            data_input=self.size,
            data_output=service.processing_output if service else self.size,
        )

        self._link_hops.append(link_hop)

    @property
    def queue_delay_total(self):
        return sum(h.queue_delay for h in self._link_hops)

    @property
    def transmission_delay_total(self):
        return sum(h.transmission_delay for h in self._link_hops)

    @property
    def processing_delay_total(self):
        return sum(h.processing_delay for h in self._link_hops)

    @property
    def propagation_delay_total(self):
        return sum(h.propagation_delay for h in self._link_hops)

    @property
    def total_delay(self):
        return sum(h.queue_delay + h.transmission_delay + h.processing_delay + h.propagation_delay for h in self._link_hops)
