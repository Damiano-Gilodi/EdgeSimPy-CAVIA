"""Plot the topology of the network."""

import matplotlib.pyplot as plt
import networkx as nx  # type: ignore
import matplotlib.patches as mpatches
from typing import cast

from edge_sim_py.components.application import Application
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.container_registry import ContainerRegistry
from edge_sim_py.components.service import Service
from edge_sim_py.components.topology import Topology


def plot_topology():

    G = cast(nx.Graph, Topology.first())

    positions = {}
    labels = {}
    sizes = []
    colors = []

    # --- Nodi principali (switch, basestation, ecc.) ---
    for node in G.nodes():
        positions[node] = node.coordinates
        labels[node] = f"BS {node.id}\n {node.coordinates}"
        sizes.append(1200)
        colors.append("#34495E")

    plt.figure(figsize=(10, 6))
    plt.title("Topology", fontsize=15, fontweight="bold", pad=20)

    # --- Disegno della rete principale ---
    nx.draw(
        G,
        pos=positions,
        node_color=colors,
        node_size=sizes,
        labels=labels,
        font_size=8,
        font_weight="bold",
        font_color="white",
        edgecolors="black",
    )

    # --- Etichette dei link ---
    edge_labels = {(u, v): f"d={data['delay']}, bw={data['bandwidth']}" for u, v, data in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos=positions, edge_labels=edge_labels, font_color="royalblue", font_size=7)

    # --- Edge Servers ---
    for bs in BaseStation.all():
        for i, es in enumerate(bs.edge_servers):
            offset_x = bs.coordinates[0] + 0.16 + (i * 0.08)
            offset_y = bs.coordinates[1] + 0.16 + (i * 0.08)
            plt.scatter(offset_x, offset_y, s=600, c="#F39C12", edgecolors="black", zorder=5)
            plt.text(
                offset_x,
                offset_y,
                f"ES {es.id}",
                fontsize=7.5,
                ha="center",
                va="center",
                fontweight="bold",
                color="black",
                zorder=6,
            )

    # --- Users ---
    for bs in BaseStation.all():
        for j, user in enumerate(bs.users):
            offset_x = bs.coordinates[0] - 0.18 - (j * 0.08)
            offset_y = bs.coordinates[1] - 0.18 - (j * 0.08)
            plt.scatter(offset_x, offset_y, s=400, c="#5DADE2", edgecolors="black", zorder=6)
            if hasattr(user, "applications") and user.applications:
                app_names = ", ".join(["app: " + (app.label if app.label != "" else str(app.id)) for app in user.applications])
            else:
                app_names = "no app"
            plt.text(
                offset_x - 0.08,
                offset_y + 0.08,
                f"U{user.id}\n{app_names}",
                fontsize=7.5,
                ha="center",
                color="black",
                fontweight="bold",
                bbox=dict(
                    facecolor="white",
                    edgecolor="none",
                    boxstyle="round,pad=0.3",
                    alpha=0.8,
                ),
            )

    # --- Services ---
    for bs in BaseStation.all():
        for i, es in enumerate(bs.edge_servers):
            es_x = bs.coordinates[0] + 0.15 + (i * 0.08)
            es_y = bs.coordinates[1] + 0.35 + (i * 0.08)
            services_here = [s for s in Service.all() if hasattr(s, "server") and s.server == es]
            for k, service in enumerate(services_here):
                s_x = es_x - 0.10 - (k * 0.70)
                s_y = es_y
                plt.scatter(s_x, s_y, s=380, c="#D2B4DE", edgecolors="black", zorder=6)
                plt.text(
                    s_x,
                    s_y + 0.08,
                    f"S{service.id}\n d:{getattr(service, 'processing_time', 0)}\n s: {getattr(service, 'processing_output', 0)}",
                    fontsize=8,
                    ha="center",
                    color="#4A235A",
                    fontweight="bold",
                    bbox=dict(
                        facecolor="white",
                        edgecolor="none",
                        boxstyle="round,pad=0.3",
                        alpha=0.9,
                    ),
                )

    # --- Container Registries ---
    for bs in BaseStation.all():
        for i, es in enumerate(bs.edge_servers):
            # Trovo tutti i container associati a questo edge server
            containers_here = [c for c in ContainerRegistry.all() if getattr(c, "server", None) == es]
            for k, registry in enumerate(containers_here):
                # Offset relativo all'ES
                c_x = bs.coordinates[0] + 0.16 + (i * 0.08) + 0.1 + (k * 0.08)
                c_y = bs.coordinates[1] - 0.16 + (i * 0.08)
                plt.scatter(c_x, c_y, s=600, c="#27AE60", edgecolors="black", zorder=5)
                plt.text(
                    c_x,
                    c_y + 0.10,
                    f"CR {registry.id}",
                    fontsize=7.5,
                    ha="center",
                    fontweight="bold",
                    color="darkgreen",
                    bbox=dict(
                        facecolor="honeydew",
                        edgecolor="none",
                        boxstyle="round,pad=0.3",
                        alpha=0.8,
                    ),
                )

    # --- Applicazioni e servizi (textbox in basso) ---
    app_text_lines = []
    for app in Application.all():
        service_labels = [f"S{srv.id}({srv.label})" for srv in app.services]
        services_str = ", ".join(service_labels) if service_labels else "no services"
        app_text_lines.append(f"App {app.id} ({app.label}): {services_str}")

    if app_text_lines:
        final_text = "\n".join(app_text_lines)

        plt.gcf().text(
            0.01,
            -0.05,  # posizione sotto la figura
            final_text,
            fontsize=9,
            ha="left",
            va="top",
            fontweight="bold",
            bbox=dict(
                facecolor="white",
                edgecolor="black",
                boxstyle="round,pad=0.4",
                alpha=0.85,
            ),
        )

    # Legenda
    legend_elements = [
        mpatches.Patch(color="#34495E", label="Base Station"),
        mpatches.Patch(color="#F39C12", label="Edge Server"),
        mpatches.Patch(color="#5DADE2", label="User"),
        mpatches.Patch(color="#BB8FCE", label="Service"),
        mpatches.Patch(color="#27AE60", label="Container Registry"),
    ]
    plt.legend(
        handles=legend_elements,
        loc="upper right",
        fontsize=9,
        frameon=True,
        fancybox=True,
    )

    plt.axis("off")
    plt.tight_layout()
    plt.show()
