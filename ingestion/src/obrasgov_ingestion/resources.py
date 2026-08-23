from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceSpec:
    name: str
    endpoint: str
    raw_table: str
    paginated: bool


RESOURCE_REGISTRY = (
    ResourceSpec(
        name="data-atualizacao",
        endpoint="data-atualizacao",
        raw_table="obrasgov_source_update_raw",
        paginated=False,
    ),
    ResourceSpec(
        name="projeto-investimento",
        endpoint="projeto-investimento",
        raw_table="obrasgov_project_raw",
        paginated=True,
    ),
    ResourceSpec(
        name="geometria",
        endpoint="geometria",
        raw_table="obrasgov_geometry_raw",
        paginated=True,
    ),
    ResourceSpec(
        name="contrato",
        endpoint="contrato",
        raw_table="obrasgov_contract_raw",
        paginated=True,
    ),
    ResourceSpec(
        name="empenho",
        endpoint="empenho",
        raw_table="obrasgov_commitment_raw",
        paginated=True,
    ),
    ResourceSpec(
        name="execucao-fisica",
        endpoint="execucao-fisica",
        raw_table="obrasgov_physical_execution_raw",
        paginated=True,
    ),
    ResourceSpec(
        name="historico-situacao-cancelada-paralisada",
        endpoint="historico-situacao-cancelada-paralisada",
        raw_table="obrasgov_status_history_raw",
        paginated=True,
    ),
    ResourceSpec(
        name="estudo-viabilidade",
        endpoint="estudo-viabilidade",
        raw_table="obrasgov_feasibility_study_raw",
        paginated=True,
    ),
)

RESOURCE_REGISTRY_BY_NAME = {resource.name: resource for resource in RESOURCE_REGISTRY}
SOURCE_UPDATE_RESOURCE = RESOURCE_REGISTRY[0].name
PAGINATED_RESOURCES = tuple(
    resource.name for resource in RESOURCE_REGISTRY if resource.paginated
)
