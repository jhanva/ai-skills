"""
cg_analyze.py — Clustering, analisis y reporte del grafo.

Todo con stdlib. Clustering via Louvain (modularidad) implementado en puro
Python, deterministico (orden de nodos estable, sin aleatoriedad).
"""

from collections import defaultdict, deque


# ---------------------------------------------------------------------------
# Estructura de grafo minima (adyacencia no dirigida con pesos)
# ---------------------------------------------------------------------------

def build_adjacency(nodes, edges):
    """Devuelve (adj, degree, m2). adj[u][v] = peso acumulado."""
    adj = {n["id"]: {} for n in nodes}
    for e in edges:
        u, v = e["source"], e["target"]
        if u not in adj or v not in adj or u == v:
            continue
        w = float(e.get("confidence_score") or 1.0)
        adj[u][v] = adj[u].get(v, 0.0) + w
        adj[v][u] = adj[v].get(u, 0.0) + w
    degree = {u: sum(nbrs.values()) for u, nbrs in adj.items()}
    m2 = sum(degree.values())  # 2m
    return adj, degree, m2


# ---------------------------------------------------------------------------
# Louvain — deteccion de comunidades por modularidad
# ---------------------------------------------------------------------------

def louvain(nodes, edges, max_passes=10):
    """Devuelve dict node_id -> community_id (enteros desde 0).

    Implementacion estandar en dos fases: optimizacion local + agregacion,
    repetida hasta que la modularidad no mejora. Deterministica: los nodos
    se recorren en orden estable.
    """
    node_ids = sorted(n["id"] for n in nodes)
    adj, degree, m2 = build_adjacency(nodes, edges)
    if m2 == 0:
        return {nid: i for i, nid in enumerate(node_ids)}

    # mapeo actual: nodo original -> super-nodo del nivel actual
    membership = {nid: nid for nid in node_ids}

    for _ in range(max_passes):
        comm = {u: u for u in adj}          # super-nodo -> comunidad
        comm_degree = dict(degree)          # suma de grados por comunidad
        improved = _local_move(adj, degree, m2, comm, comm_degree)
        if not improved:
            break
        # relabel comunidades a ids compactos
        labels = {}
        for u in sorted(adj):
            c = comm[u]
            if c not in labels:
                labels[c] = len(labels)
        comm = {u: labels[comm[u]] for u in adj}
        # actualizar membership de nodos originales
        membership = {nid: comm[membership[nid]] for nid in node_ids}
        # agregar: construir grafo de comunidades. Los edges internos se
        # preservan como self-loops (cuentan en el grado del super-nodo,
        # necesario para que la modularidad del siguiente nivel sea correcta)
        new_adj = defaultdict(lambda: defaultdict(float))
        for u, nbrs in adj.items():
            cu = comm[u]
            for v, w in nbrs.items():
                new_adj[cu][comm[v]] += w
        adj = {c: dict(nbrs) for c, nbrs in new_adj.items()}
        for c in set(comm.values()):
            adj.setdefault(c, {})
        degree = {u: sum(nbrs.values()) for u, nbrs in adj.items()}

    membership = _absorb_tiny(node_ids, edges, membership, min_size=3)

    # relabel final compacto por orden de aparicion
    labels = {}
    result = {}
    for nid in node_ids:
        c = membership[nid]
        if c not in labels:
            labels[c] = len(labels)
        result[nid] = labels[c]
    return result


def _absorb_tiny(node_ids, edges, membership, min_size=3):
    """Post-pase: comunidades con menos de min_size nodos se absorben en
    la comunidad vecina con la que mas edges comparten (si existe)."""
    for _ in range(3):
        sizes = defaultdict(int)
        for nid in node_ids:
            sizes[membership[nid]] += 1
        tiny = {c for c, s in sizes.items() if s < min_size}
        if not tiny:
            break
        # edges de cada comunidad tiny hacia comunidades vecinas
        outward = defaultdict(lambda: defaultdict(int))
        for e in edges:
            cu = membership.get(e["source"])
            cv = membership.get(e["target"])
            if cu is None or cv is None or cu == cv:
                continue
            if cu in tiny:
                outward[cu][cv] += 1
            if cv in tiny:
                outward[cv][cu] += 1
        moved = False
        for c in sorted(tiny):
            if not outward[c]:
                continue  # componente aislado: se queda como esta
            best = max(sorted(outward[c]), key=lambda k: outward[c][k])
            for nid in node_ids:
                if membership[nid] == c:
                    membership[nid] = best
                    moved = True
        if not moved:
            break
    return membership


def _local_move(adj, degree, m2, comm, comm_degree):
    """Fase 1 de Louvain: mover nodos a la comunidad vecina que maximiza
    la ganancia de modularidad. Modifica comm/comm_degree in place."""
    improved_any = False
    for _ in range(20):  # iteraciones hasta estabilizar
        moved = False
        for u in sorted(adj):
            cu = comm[u]
            ku = degree[u]
            # peso hacia cada comunidad vecina
            weights = defaultdict(float)
            for v, w in adj[u].items():
                weights[comm[v]] += w
            # sacar u de su comunidad
            comm_degree[cu] -= ku
            best_c, best_gain = cu, 0.0
            for c, w_in in sorted(weights.items()):
                gain = w_in - comm_degree[c] * ku / m2
                if gain > best_gain + 1e-12:
                    best_gain, best_c = gain, c
            comm_degree[best_c] = comm_degree.get(best_c, 0.0) + ku
            if best_c != cu:
                comm[u] = best_c
                moved = True
                improved_any = True
        if not moved:
            break
    return improved_any


def cohesion_scores(nodes, edges, communities):
    """Cohesion por comunidad: edges internos / edges totales que la tocan."""
    internal = defaultdict(int)
    total = defaultdict(int)
    for e in edges:
        cu = communities.get(e["source"])
        cv = communities.get(e["target"])
        if cu is None or cv is None:
            continue
        total[cu] += 1
        if cu != cv:
            total[cv] += 1
        else:
            internal[cu] += 1
    return {c: round(internal[c] / total[c], 2) if total[c] else 0.0
            for c in set(communities.values())}


# ---------------------------------------------------------------------------
# Analisis: god nodes, sorpresas, betweenness, preguntas
# ---------------------------------------------------------------------------

def god_nodes(nodes, edges, top=10):
    deg = defaultdict(int)
    for e in edges:
        deg[e["source"]] += 1
        deg[e["target"]] += 1
    labels = {n["id"]: n["label"] for n in nodes}
    ranked = sorted(((d, nid) for nid, d in deg.items() if nid in labels),
                    key=lambda x: (-x[0], x[1]))
    return [{"id": nid, "label": labels[nid], "degree": d}
            for d, nid in ranked[:top]]


def surprising_connections(nodes, edges, communities, top=8):
    """Edges INFERRED que cruzan comunidades o archivos distintos."""
    labels = {n["id"]: n["label"] for n in nodes}
    files = {n["id"]: n.get("source_file") for n in nodes}
    scored = []
    for e in edges:
        u, v = e["source"], e["target"]
        if u not in labels or v not in labels:
            continue
        score = 0
        if e["confidence"] == "INFERRED":
            score += 2
        if communities.get(u) != communities.get(v):
            score += 2
        if files.get(u) and files.get(v) and files[u] != files[v]:
            score += 1
        if e["relation"] in ("references", "semantically_similar_to"):
            score += 1
        if score >= 3:
            scored.append((score, e))
    scored.sort(key=lambda x: (-x[0], x[1]["source"], x[1]["target"]))
    out = []
    for score, e in scored[:top]:
        out.append({
            "source": labels[e["source"]],
            "target": labels[e["target"]],
            "relation": e["relation"],
            "confidence": e["confidence"],
            "source_file": files.get(e["source"]),
            "target_file": files.get(e["target"]),
            "communities": (communities.get(e["source"]),
                            communities.get(e["target"])),
        })
    return out


def betweenness(nodes, edges, sample_cap=300):
    """Betweenness centrality (Brandes, sin pesos). Si el grafo supera
    sample_cap nodos, muestrea fuentes de forma deterministica."""
    adj = defaultdict(set)
    for e in edges:
        u, v = e["source"], e["target"]
        if u != v:
            adj[u].add(v)
            adj[v].add(u)
    vertices = sorted(adj)
    n = len(vertices)
    if n == 0:
        return {}
    if n > sample_cap:
        step = max(1, n // sample_cap)
        sources = vertices[::step]
    else:
        sources = vertices
    bc = dict.fromkeys(vertices, 0.0)
    for s in sources:
        # BFS de Brandes
        stack, preds, sigma, dist = [], defaultdict(list), \
            defaultdict(float), {}
        sigma[s], dist[s] = 1.0, 0
        queue = deque([s])
        while queue:
            v = queue.popleft()
            stack.append(v)
            for w in adj[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    preds[w].append(v)
        delta = defaultdict(float)
        while stack:
            w = stack.pop()
            for v in preds[w]:
                delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]
        # normalizacion aproximada
    norm = (n - 1) * (n - 2) or 1
    scale = n / max(1, len(sources))  # compensa el muestreo
    return {v: round(b * scale / norm, 4) for v, b in bc.items()}


def suggest_questions(nodes, edges, communities, comm_labels, top=6):
    """Preguntas que el grafo puede responder: puentes cross-community
    por betweenness + hubs de edges INFERRED que conviene verificar."""
    labels = {n["id"]: n["label"] for n in nodes}
    bc = betweenness(nodes, edges)
    questions = []

    # puentes: nodos con alta betweenness que conectan comunidades distintas
    neighbor_comms = defaultdict(set)
    for e in edges:
        cu = communities.get(e["source"])
        cv = communities.get(e["target"])
        if cu is not None and cv is not None and cu != cv:
            neighbor_comms[e["source"]].add(cv)
            neighbor_comms[e["target"]].add(cu)
    bridges = sorted(
        ((bc.get(nid, 0), nid) for nid in neighbor_comms if nid in labels),
        key=lambda x: (-x[0], x[1]))
    for score, nid in bridges[:3]:
        if score <= 0:
            continue
        own = comm_labels.get(communities.get(nid),
                              str(communities.get(nid)))
        others = ", ".join(sorted(
            comm_labels.get(c, str(c)) for c in neighbor_comms[nid]))
        questions.append({
            "question": f"Por que {labels[nid]} conecta '{own}' con "
                        f"'{others}'?",
            "reason": f"Betweenness {score} - es un puente entre "
                      f"comunidades.",
        })

    # hubs INFERRED: nodos con mas edges inferidos (verificables)
    inferred = defaultdict(list)
    for e in edges:
        if e["confidence"] == "INFERRED":
            inferred[e["source"]].append(e)
            inferred[e["target"]].append(e)
    hubs = sorted(inferred.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for nid, elist in hubs[:top - len(questions)]:
        if nid not in labels or len(elist) < 2:
            continue
        peers = []
        for e in elist[:2]:
            other = e["target"] if e["source"] == nid else e["source"]
            if other in labels:
                peers.append(labels[other])
        questions.append({
            "question": f"Son correctas las {len(elist)} relaciones "
                        f"inferidas de {labels[nid]}"
                        + (f" (ej. con {' y '.join(peers)})" if peers else "")
                        + "?",
            "reason": f"{len(elist)} edges INFERRED - conexiones deducidas "
                      f"que conviene verificar.",
        })
    return questions[:top]


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------

def render_report(meta, nodes, edges, communities, comm_labels, cohesion,
                  gods, surprises, questions, health):
    total_e = len(edges) or 1
    by_conf = defaultdict(int)
    for e in edges:
        by_conf[e["confidence"]] += 1
    pct = {k: round(100 * v / total_e) for k, v in by_conf.items()}

    comm_members = defaultdict(list)
    labels = {n["id"]: n["label"] for n in nodes}
    for nid, c in communities.items():
        if nid in labels:
            comm_members[c].append(labels[nid])

    lines = []
    lines.append(f"# Graph Report - {meta['root']}  ({meta['date']})")
    lines.append("")
    lines.append("## Corpus")
    lines.append(f"- {meta['total_files']} archivos analizados"
                 f" ({meta['skipped']} omitidos)")
    cats = " · ".join(f"{k}: {v}" for k, v in
                      sorted(meta["by_category"].items()) if v)
    if cats:
        lines.append(f"- {cats}")
    lines.append("")
    lines.append("## Resumen")
    lines.append(f"- {len(nodes)} nodos · {len(edges)} edges · "
                 f"{len(comm_members)} comunidades")
    lines.append(f"- Confianza: {pct.get('EXTRACTED', 0)}% EXTRACTED · "
                 f"{pct.get('INFERRED', 0)}% INFERRED · "
                 f"{pct.get('AMBIGUOUS', 0)}% AMBIGUOUS")
    if health.get("dropped_ambiguous"):
        lines.append(f"- {health['dropped_ambiguous']} llamadas ambiguas "
                     f"descartadas (multiples definiciones, sin inventar edges)")
    if health.get("dangling"):
        lines.append(f"- ADVERTENCIA: {health['dangling']} edges con extremos "
                     f"inexistentes fueron eliminados")
    lines.append("")
    lines.append("## God Nodes (los mas conectados - abstracciones centrales)")
    for i, g in enumerate(gods, 1):
        lines.append(f"{i}. `{g['label']}` - {g['degree']} edges")
    lines.append("")
    lines.append("## Conexiones sorprendentes (cruces que no son obvios)")
    if not surprises:
        lines.append("_Ninguna detectada._")
    for s in surprises:
        cu, cv = s["communities"]
        bridge = ""
        if cu != cv:
            lu = comm_labels.get(cu, str(cu))
            lv = comm_labels.get(cv, str(cv))
            bridge = f"  _Puente: {lu} -> {lv}_"
        lines.append(f"- `{s['source']}` --{s['relation']}--> "
                     f"`{s['target']}`  [{s['confidence']}]{bridge}")
        if s["source_file"] and s["target_file"] \
                and s["source_file"] != s["target_file"]:
            lines.append(f"  {s['source_file']} -> {s['target_file']}")
    lines.append("")
    lines.append("## Comunidades")
    ranked_comms = sorted(comm_members,
                          key=lambda c: (-len(comm_members[c]), c))
    shown_comms = ranked_comms[:20]
    for c in shown_comms:
        name = comm_labels.get(c, f"Comunidad {c}")
        members = sorted(comm_members[c])
        shown = ", ".join(members[:12])
        more = f" (+{len(members) - 12} mas)" if len(members) > 12 else ""
        lines.append("")
        lines.append(f"### Comunidad {c} - \"{name}\"")
        lines.append(f"Cohesion: {cohesion.get(c, 0)}")
        lines.append(f"Nodos ({len(members)}): {shown}{more}")
    rest = len(ranked_comms) - len(shown_comms)
    if rest > 0:
        rest_nodes = sum(len(comm_members[c])
                         for c in ranked_comms[len(shown_comms):])
        lines.append("")
        lines.append(f"_...y {rest} comunidades menores "
                     f"({rest_nodes} nodos), en su mayoria archivos "
                     f"aislados sin conexiones entre si._")
    lines.append("")
    lines.append("## Preguntas sugeridas")
    lines.append("_Preguntas que este grafo puede responder:_")
    lines.append("")
    for q in questions:
        lines.append(f"- **{q['question']}**")
        lines.append(f"  _{q['reason']}_")
    lines.append("")
    return "\n".join(lines)
