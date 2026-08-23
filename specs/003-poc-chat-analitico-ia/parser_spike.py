from __future__ import annotations

import sqlglot
from sqlglot import exp

ALLOWED_VIEWS = {
    ("gold", "vw_market_overview_current"),
    ("gold", "vw_project_investment_current"),
    ("gold", "vw_project_location_current"),
    ("gold", "vw_status_distribution_current"),
}
ALLOWED_FUNCTIONS = {
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "COALESCE",
    "NULLIF",
    "ROUND",
    "DATE_TRUNC",
    "DATE_PART",
}


def validate(sql: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    statements = sqlglot.parse(sql, read="postgres")
    if len(statements) != 1:
        return False, ["multiple_statements"]

    statement = statements[0]
    if not isinstance(statement, exp.Select):
        reasons.append("root_not_select")
    def has_node(name: str) -> bool:
        node_type = getattr(exp, name, None)
        return node_type is not None and statement.find(node_type) is not None

    if has_node("Create"):
        reasons.append("create")
    if has_node("Insert"):
        reasons.append("insert")
    if has_node("Update"):
        reasons.append("update")
    if has_node("Delete"):
        reasons.append("delete")
    if has_node("Merge"):
        reasons.append("merge")
    if has_node("Command"):
        reasons.append("command")
    if has_node("Lock"):
        reasons.append("lock")
    if has_node("Into"):
        reasons.append("select_into")
    if has_node("Join"):
        reasons.append("join")
    if has_node("Lateral"):
        reasons.append("lateral")
    if any(
        node.__class__.__name__ in {"TableFunction", "Unnest", "Explode"}
        for node in statement.walk()
    ):
        reasons.append("table_function")
    if has_node("Star"):
        reasons.append("wildcard")
    for function in statement.find_all(exp.Func):
        if function.sql_name().upper() not in ALLOWED_FUNCTIONS:
            reasons.append("function_not_allowlisted")
            break

    with_node = statement.args.get("with_") or statement.args.get("with")
    if with_node and with_node.args.get("recursive"):
        reasons.append("recursive_cte")

    cte_names = {
        cte.alias_or_name.lower()
        for cte in statement.find_all(exp.CTE)
    }
    physical_tables = {
        (table.db.lower(), table.name.lower())
        for table in statement.find_all(exp.Table)
        if table.name.lower() not in cte_names
    }
    if not physical_tables:
        reasons.append("no_physical_gold_view")
    if not physical_tables.issubset(ALLOWED_VIEWS):
        reasons.append("view_not_allowlisted")
    if len(physical_tables) > 1:
        reasons.append("more_than_one_physical_view")

    return not reasons, reasons


CASES = {
    "valid_simple_select": (
        "SELECT source_status, count(DISTINCT project_id) AS project_count "
        "FROM gold.vw_market_overview_current GROUP BY source_status",
        True,
    ),
    "valid_read_only_cte": (
        "WITH filtered AS (SELECT project_id, planned_investment_amount "
        "FROM gold.vw_market_overview_current WHERE planned_investment_amount > 0) "
        "SELECT count(DISTINCT project_id) AS projects, sum(planned_investment_amount) AS total "
        "FROM filtered",
        True,
    ),
    "reject_create_temp": (
        "CREATE TEMP TABLE scratch AS SELECT project_id FROM gold.vw_market_overview_current",
        False,
    ),
    "reject_dml": (
        "DELETE FROM gold.vw_market_overview_current",
        False,
    ),
    "reject_multiple_statements": (
        "SELECT count(*) FROM gold.vw_market_overview_current; "
        "SELECT count(*) FROM gold.vw_status_distribution_current",
        False,
    ),
    "reject_wildcard": (
        "SELECT * FROM gold.vw_market_overview_current",
        False,
    ),
    "reject_join": (
        "SELECT count(*) FROM gold.vw_market_overview_current m "
        "JOIN gold.vw_status_distribution_current s ON true",
        False,
    ),
    "reject_recursive_cte": (
        "WITH RECURSIVE x AS (SELECT 1 UNION ALL SELECT 1) SELECT * FROM x",
        False,
    ),
    "reject_catalog": (
        "SELECT table_name FROM information_schema.tables",
        False,
    ),
    "reject_select_into": (
        "SELECT project_id INTO scratch FROM gold.vw_market_overview_current",
        False,
    ),
    "reject_cte_write": (
        "WITH changed AS (DELETE FROM gold.vw_market_overview_current RETURNING project_id) "
        "SELECT project_id FROM changed",
        False,
    ),
    "reject_lock": (
        "SELECT project_id FROM gold.vw_market_overview_current FOR UPDATE",
        False,
    ),
    "reject_forbidden_function": (
        "SELECT pg_sleep(1) FROM gold.vw_market_overview_current",
        False,
    ),
}


for name, (sql, expected) in CASES.items():
    actual, reasons = validate(sql)
    outcome = "PASS" if actual == expected else "FAIL"
    print(f"{outcome} {name}: accepted={actual} reasons={','.join(reasons) or '-'}")
    if outcome == "FAIL":
        raise SystemExit(1)

print(
    f"SUMMARY cases={len(CASES)} passed={len(CASES)} "
    f"parser=sqlglot-{sqlglot.__version__} dialect=postgres"
)
