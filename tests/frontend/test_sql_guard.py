from __future__ import annotations

import pytest

from frontend.analytical_chat.sql_guard import (
    GuardLimits,
    SQLGuard,
    SQLGuardError,
    check_sql,
    validate_sql,
)


def _reject(sql: str, reason: str) -> None:
    with pytest.raises(SQLGuardError) as error:
        validate_sql(sql)
    assert reason in error.value.reasons


def test_accepts_gold_aggregations_and_read_only_cte() -> None:
    result = validate_sql(
        """
        WITH filtered AS (
            SELECT project_id, planned_investment_amount
            FROM gold.vw_market_overview_current
            WHERE planned_investment_amount > 0
        )
        SELECT count(DISTINCT project_id) AS project_count,
               sum(planned_investment_amount) AS planned_total
        FROM filtered
        """
    )

    assert result.view_name == "gold.vw_market_overview_current"


def test_accepts_boolean_text_filters_without_treating_operators_as_functions() -> None:
    result = validate_sql(
        """
        SELECT project_id, organization_name, planned_investment_amount
        FROM gold.vw_market_overview_current
        WHERE organization_name ILIKE '%Vertere%'
          AND planned_investment_amount IS NOT NULL
        ORDER BY planned_investment_amount DESC
        LIMIT 1
        """
    )

    assert result.view_name == "gold.vw_market_overview_current"


def test_accepts_location_ranking_only_by_distinct_projects() -> None:
    result = validate_sql(
        """
        SELECT municipality_name, count(DISTINCT project_id) AS project_count
        FROM gold.vw_project_location_current
        GROUP BY municipality_name
        ORDER BY project_count DESC
        """
    )

    assert result.view_name == "gold.vw_project_location_current"


def test_accepts_status_distribution_contract_without_recounting() -> None:
    result = validate_sql(
        """
        SELECT source_status, project_count
        FROM gold.vw_status_distribution_current
        ORDER BY project_count DESC
        """
    )

    assert result.view_name == "gold.vw_status_distribution_current"


@pytest.mark.parametrize(
    ("sql", "reason"),
    [
        (
            "CREATE TEMP TABLE x AS SELECT project_id FROM gold.vw_market_overview_current",
            "root_not_select",
        ),
        ("SELECT project_id FROM gold.vw_market_overview_current; SELECT 1", "multiple_statements"),
        ("SELECT * FROM gold.vw_market_overview_current", "wildcard"),
        (
            "SELECT count(DISTINCT m.project_id) FROM gold.vw_market_overview_current m "
            "JOIN gold.vw_status_distribution_current s ON true",
            "join",
        ),
        (
            "WITH RECURSIVE x AS (SELECT project_id FROM gold.vw_market_overview_current) "
            "SELECT project_id FROM x",
            "recursive_cte",
        ),
        ("SELECT table_name FROM information_schema.tables", "schema_not_allowlisted"),
        ("SELECT project_id INTO scratch FROM gold.vw_market_overview_current", "select_into"),
        ("SELECT project_id FROM gold.vw_market_overview_current FOR UPDATE", "lock"),
        ("SELECT pg_sleep(1) FROM gold.vw_market_overview_current", "function_not_allowlisted"),
        ("SELECT secret_column FROM gold.vw_market_overview_current", "column_not_allowlisted"),
        ("SELECT project_id FROM vw_market_overview_current", "schema_not_allowlisted"),
        (
            "WITH changed AS (DELETE FROM gold.vw_market_overview_current RETURNING project_id) "
            "SELECT project_id FROM changed",
            "forbidden_statement",
        ),
        (
            "SELECT count(project_id) FROM gold.vw_market_overview_current",
            "count_must_distinct_project_id",
        ),
        (
            "SELECT municipality_name, sum(planned_investment_amount) "
            "FROM gold.vw_project_location_current GROUP BY municipality_name",
            "financial_aggregation_on_location",
        ),
        (
            "SELECT project_id FROM gold.vw_market_overview_current "
            "UNION SELECT project_id FROM gold.vw_market_overview_current",
            "set_operation",
        ),
    ],
)
def test_rejects_unsafe_or_semantically_invalid_sql(sql: str, reason: str) -> None:
    _reject(sql, reason)


def test_accepts_multiple_allowlisted_physical_views_through_ctes() -> None:
    result = validate_sql(
        """
        WITH market AS (
            SELECT project_id FROM gold.vw_market_overview_current
        ), status AS (
            SELECT source_status FROM gold.vw_status_distribution_current
        )
        SELECT project_id FROM market
        """
    )

    assert result.view_names == (
        "gold.vw_market_overview_current",
        "gold.vw_status_distribution_current",
    )


def test_accepts_project_to_contract_join_and_aggregation() -> None:
    result = validate_sql(
        """
        SELECT m.organization_name, max(c.valor_global_contrato) AS maior_contrato
        FROM gold.vw_market_overview_current AS m
        LEFT JOIN gold.vw_project_contract_current AS c
            ON m.project_id = c.project_id
        GROUP BY m.organization_name
        """
    )

    assert set(result.view_names) == {
        "gold.vw_market_overview_current",
        "gold.vw_project_contract_current",
    }


def test_accepts_child_joins_only_after_project_preaggregation() -> None:
    result = validate_sql(
        """
        WITH contracts AS (
            SELECT project_id, max(valor_global_contrato) AS maior_contrato
            FROM gold.vw_project_contract_current
            GROUP BY project_id
        ), commitments AS (
            SELECT project_id, sum(valor_empenho) AS empenhado
            FROM gold.vw_project_commitment_current
            GROUP BY project_id
        )
        SELECT contracts.project_id, maior_contrato, empenhado
        FROM contracts
        INNER JOIN commitments ON contracts.project_id = commitments.project_id
        """
    )

    assert len(result.view_names) == 2


def test_accepts_distinct_project_cte_as_preaggregation() -> None:
    sql = (
        "WITH exec AS ("
        "SELECT project_id FROM gold.vw_project_execution_current "
        "WHERE physical_execution_percentage > 80 GROUP BY project_id"
        "), loc AS ("
        "SELECT DISTINCT project_id FROM gold.vw_project_location_current "
        "WHERE municipality_name ILIKE 'Fortaleza'"
        "), proj AS ("
        "SELECT project_id FROM gold.vw_market_overview_current "
        "WHERE source_status = 'Em execução'"
        ") SELECT COUNT(DISTINCT p.project_id) AS total_obras "
        "FROM proj AS p INNER JOIN loc AS l ON p.project_id = l.project_id "
        "INNER JOIN exec AS e ON p.project_id = e.project_id"
    )

    assert validate_sql(sql).sql == sql


def test_rejects_raw_child_to_child_join_and_parent_fanout_measure() -> None:
    _reject(
        """
        SELECT c.project_id, c.valor_global_contrato, e.valor_empenho
        FROM gold.vw_project_contract_current AS c
        JOIN gold.vw_project_commitment_current AS e
            ON c.project_id = e.project_id
        """,
        "join_fanout_requires_preaggregation",
    )
    _reject(
        """
        SELECT sum(m.planned_investment_amount)
        FROM gold.vw_market_overview_current AS m
        JOIN gold.vw_project_contract_current AS c
            ON m.project_id = c.project_id
        """,
        "financial_aggregation_after_fanout",
    )


@pytest.mark.parametrize(
    ("view_name", "column"),
    [
        ("gold.vw_market_overview_current", "organization_name"),
        ("gold.vw_project_investment_current", "funding_source_name"),
        ("gold.vw_project_location_current", "municipality_name"),
        ("gold.vw_status_distribution_current", "source_status"),
        ("gold.vw_project_detail_current", "global_goal_description"),
        ("gold.vw_project_participant_current", "participant_role"),
        ("gold.vw_project_axis_type_current", "type_name"),
        ("gold.vw_project_ppa_current", "ppa_description"),
        ("gold.vw_project_restriction_area_current", "restriction_area"),
        ("gold.vw_project_photo_indicator_current", "ind_foto"),
        ("gold.vw_project_contract_current", "valor_global_contrato"),
        ("gold.vw_project_commitment_current", "pago"),
        ("gold.vw_project_commitment_totals_current", "commitment_count"),
        ("gold.vw_project_execution_current", "physical_execution_percentage"),
        ("gold.vw_project_status_history_current", "justification"),
        ("gold.vw_project_feasibility_study_current", "study_type"),
        ("gold.vw_project_coverage_current", "coverage_status"),
    ],
)
def test_accepts_each_dashboard_gold_view(view_name: str, column: str) -> None:
    result = validate_sql(f"SELECT {column} FROM {view_name} LIMIT 5")

    assert result.view_names == (view_name,)


def test_accepts_project_counts_across_dashboard_relations() -> None:
    result = validate_sql(
        """
        WITH contracts AS (
            SELECT project_id, count(DISTINCT contract_source_id) AS contract_count
            FROM gold.vw_project_contract_current
            GROUP BY project_id
        ), participants AS (
            SELECT project_id, count(DISTINCT organization_key) AS participant_count
            FROM gold.vw_project_participant_current
            GROUP BY project_id
        )
        SELECT m.organization_name, sum(contracts.contract_count) AS contract_count,
               sum(participants.participant_count) AS participant_count
        FROM gold.vw_market_overview_current AS m
        LEFT JOIN contracts ON m.project_id = contracts.project_id
        LEFT JOIN participants ON m.project_id = participants.project_id
        GROUP BY m.organization_name
        """
    )

    assert len(result.view_names) == 3


def test_rejects_complexity_limits_closed() -> None:
    guard = SQLGuard(limits=GuardLimits(max_sql_characters=20))
    with pytest.raises(SQLGuardError) as error:
        guard.validate("SELECT project_id FROM gold.vw_market_overview_current")
    assert "sql_too_long" in error.value.reasons


def test_check_interface_returns_reasons_without_executing_anything() -> None:
    accepted, reasons = check_sql("SELECT project_id FROM gold.vw_market_overview_current")
    rejected, rejection_reasons = check_sql("SELECT * FROM gold.vw_market_overview_current")

    assert accepted is True
    assert reasons == []
    assert rejected is False
    assert "wildcard" in rejection_reasons
