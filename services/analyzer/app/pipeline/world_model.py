from typing import Any, Dict, List, Tuple


def build_world_model(parsed: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    assets: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    asset_lookup: dict[str, int] = {}

    def add_asset(asset_type: str, name: str, properties: Dict[str, Any]) -> int:
        key = f"{asset_type}:{name}"
        if key in asset_lookup:
            return asset_lookup[key]
        assets.append({"asset_type": asset_type, "name": name, "properties": properties})
        asset_lookup[key] = len(assets) - 1
        return asset_lookup[key]

    compose = parsed.get("compose", {})
    for service in compose.get("services", []):
        service_idx = add_asset("service", service["name"], {"environment": service.get("environment", {})})
        for port in service.get("ports", []):
            port_name = f'{service["name"]}:{port["host"]}->{port["container"]}'
            port_idx = add_asset("port", port_name, port)
            edges.append({"from_index": service_idx, "relation": "exposes", "to_index": port_idx, "properties": port})

    docker = parsed.get("dockerfile")
    if docker:
        container_idx = add_asset("container", "app-container", docker)
        for port in docker.get("exposed_ports", []):
            port_idx = add_asset("port", f"docker-expose:{port}", {"container_port": port})
            edges.append(
                {
                    "from_index": container_idx,
                    "relation": "declares_port",
                    "to_index": port_idx,
                    "properties": {"source": "Dockerfile"},
                }
            )

    for route in parsed.get("routes", []):
        route_idx = add_asset("route", route["route_path"], route)
        service_idx = add_asset("service", "web", {"derived": True})
        edges.append(
            {"from_index": route_idx, "relation": "belongs_to", "to_index": service_idx, "properties": {"methods": route["methods"]}}
        )
        if route.get("is_protected"):
            middleware_idx = add_asset("middleware", "inline-auth-guard", {"type": "route-local"})
            edges.append(
                {"from_index": route_idx, "relation": "protected_by", "to_index": middleware_idx, "properties": {}}
            )

    middleware = parsed.get("middleware")
    if middleware:
        middleware_idx = add_asset("middleware", "middleware.ts", middleware)
        for prefix in middleware.get("protected_prefixes", []):
            prefix_idx = add_asset("path-prefix", prefix, {"type": "matcher"})
            edges.append(
                {
                    "from_index": middleware_idx,
                    "relation": "protects_prefix",
                    "to_index": prefix_idx,
                    "properties": {},
                }
            )

    for variable in parsed.get("env", {}).get("variables", []):
        variable_idx = add_asset("secret" if variable["is_secret_like"] else "config", variable["key"], variable)
        service_idx = add_asset("service", "web", {"derived": True})
        edges.append({"from_index": service_idx, "relation": "uses", "to_index": variable_idx, "properties": {}})

    database_idx = add_asset("database", "postgres", {"engine": "postgres"})
    service_idx = add_asset("service", "web", {"derived": True})
    edges.append({"from_index": service_idx, "relation": "connects_to", "to_index": database_idx, "properties": {"source": "lib/db.ts"}})

    return assets, edges

