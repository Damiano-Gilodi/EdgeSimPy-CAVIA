import matplotlib.pyplot as plt  # type: ignore
import matplotlib.patches as mpatches  # type: ignore
import networkx as nx  # type: ignore

from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.topology import Topology


def plot_cavia_topology():
    # Recuperiamo la topologia
    topology = Topology.first()
    # Creiamo un grafo NetworkX pulito partendo dai dati di EdgeSimPy
    G = nx.Graph()

    positions = {}

    # --- Configurazione Nodi e Posizioni ---
    for node in topology.nodes:
        G.add_node(node.id)
        # Usiamo le coordinate della BaseStation come riferimento
        bs = next((b for b in BaseStation.all() if b.id == node.id), None)
        # Moltiplichiamo le coordinate per "allargare" il grafico
        positions[node.id] = (bs.coordinates[0] * 2.5, bs.coordinates[1] * 2.5) if bs else (0, 0)

    plt.figure(figsize=(16, 12))
    plt.title("CAVIA Deployment Topology (Optimized View)", fontsize=16, fontweight="bold")

    # --- Disegno dei Link con recupero dati corretto ---
    edge_labels = {}
    for u, v in topology.edges:
        G.add_edge(u.id, v.id)

        # Recuperiamo i dati dell'arco
        edge_data = topology._adj[u][v]

        # Gestione robusta: se è un dizionario o un oggetto NetworkLink
        if isinstance(edge_data, dict):
            # Se è un dizionario, i valori sono nelle chiavi
            # Nota: usiamo 'delay' perché è quello che hai salvato nel Loader
            delay = edge_data.get("delay", "N/A")
            bw = edge_data.get("bandwidth", "N/A")
        else:
            # Se è un oggetto NetworkLink
            delay = getattr(edge_data, "delay", "N/A")
            bw = getattr(edge_data, "bandwidth", "N/A")

        edge_labels[(u.id, v.id)] = f"d:{delay}ms\nbw:{bw}"

    nx.draw_networkx_edges(G, pos=positions, alpha=0.3, edge_color="gray")
    nx.draw_networkx_edge_labels(G, pos=positions, edge_labels=edge_labels, font_size=6, font_color="blue")

    # --- Disegno Base Stations ---
    nx.draw_networkx_nodes(G, pos=positions, node_size=1000, node_color="#34495E", edgecolors="white")
    nx.draw_networkx_labels(G, pos=positions, font_color="white", font_size=8, font_weight="bold")

    # --- Edge Servers e Servizi Raggruppati ---
    for bs in BaseStation.all():
        for i, es in enumerate(bs.edge_servers):
            # Posizioniamo il server leggermente sopra la BS
            es_x, es_y = positions[bs.id][0], positions[bs.id][1] + 0.4

            # Colore basato sul sovraccarico
            color = "#E74C3C" if es.cpu_demand > es.cpu else "#F39C12"

            plt.scatter(es_x, es_y, s=1200, c=color, edgecolors="black", linewidths=1.5, zorder=5)
            plt.text(es_x, es_y, f"ES {es.id}\n{es.cpu_demand}/{es.cpu}", ha="center", va="center", fontsize=7, fontweight="bold")

            # RAGGRUPPAMENTO SERVIZI: invece di tanti cerchi, facciamo un unico box testo
            if es.services:
                service_list = "\n".join([f"• {s.label}" for s in es.services])
                plt.text(
                    es_x, es_y + 0.5, service_list, fontsize=7, bbox=dict(facecolor="#D2B4DE", alpha=0.8, boxstyle="round,pad=0.3"), ha="center", va="bottom"
                )

    # Legenda e rifiniture
    legend_elements = [
        mpatches.Patch(color="#34495E", label="Base Station"),
        mpatches.Patch(color="#F39C12", label="Edge Server (OK)"),
        mpatches.Patch(color="#E74C3C", label="Overloaded Server"),
        mpatches.Patch(color="#D2B4DE", label="Hosted Services"),
    ]
    plt.legend(handles=legend_elements, loc="upper right")
    plt.axis("off")
    plt.tight_layout()
    plt.show()
