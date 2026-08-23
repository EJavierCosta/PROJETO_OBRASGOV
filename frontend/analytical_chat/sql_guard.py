"""Validação fechada de SQL PostgreSQL gerado para o chat analítico."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from .context import GENERATABLE_COLUMNS as SEMANTIC_GENERATABLE_COLUMNS
from .context import GOLD_CATALOG

try:
    import sqlglot
    from sqlglot import exp
except ModuleNotFoundError:  # pragma: no cover - dependência do extra frontend
    sqlglot = None  # type: ignore[assignment]
    exp = None  # type: ignore[assignment]


ALLOWED_VIEWS = frozenset(SEMANTIC_GENERATABLE_COLUMNS)
GENERATABLE_COLUMNS = {
    view_name: frozenset(columns)
    for view_name, columns in SEMANTIC_GENERATABLE_COLUMNS.items()
}
_CATALOG_BY_VIEW = {contract.name: contract for contract in GOLD_CATALOG}

ALLOWED_FUNCTIONS = frozenset(
    {
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
)

_FORBIDDEN_NODE_NAMES = {
    "Command",
    "Copy",
    "Create",
    "Delete",
    "Drop",
    "Grant",
    "Insert",
    "Merge",
    "Rollback",
    "Set",
    "Transaction",
    "Truncate",
    "Update",
    "Use",
}
_TABLE_FUNCTION_NODE_NAMES = {
    "Explode",
    "GenerateSeries",
    "OpenJSON",
    "Posexplode",
    "RowsFrom",
    "TableFunction",
    "Unnest",
}
_SET_OPERATION_NAMES = {"Except", "Intersect", "Union"}
_PARAMETER_NODE_NAMES = {"Parameter", "Placeholder", "SessionParameter", "Var"}
_UNSAFE_JOIN_SIDES = {"RIGHT", "FULL"}
_COUNT_KEYS = frozenset(
    {
        "project_id",
        "contract_source_id",
        "commitment_key",
        "id_execucao_fisica",
        "study_key",
        "organization_key",
        "semantic_key",
    }
)
_FINANCIAL_FUNCTIONS = frozenset({"SUM", "AVG", "MIN", "MAX"})


@dataclass(frozen=True)
class GuardLimits:
    max_sql_characters: int = 12_000
    max_ast_nodes: int = 500
    max_ast_depth: int = 32
    max_ctes: int = 8
    max_subqueries: int = 6
    max_relations: int = 4
    max_joins: int = 3
    max_group_by_columns: int = 5
    max_aggregations: int = 8


DEFAULT_GUARD_LIMITS = GuardLimits()


class SQLGuardError(ValueError):
    """SQL rejeitado antes de chegar ao executor PostgreSQL."""

    def __init__(self, message: str = "SQL não permitido.", *, reasons: Iterable[str] = ()) -> None:
        self.reasons = tuple(dict.fromkeys(reasons))
        detail = f" ({', '.join(self.reasons)})" if self.reasons else ""
        super().__init__(f"{message}{detail}")


SqlGuardError = SQLGuardError


@dataclass(frozen=True)
class ValidatedSQL:
    """Consulta cuja árvore e gramática Gold foram aprovadas."""

    sql: str
    statement: Any
    view_name: str
    view_names: tuple[str, ...] = ()


ValidatedQuery = ValidatedSQL


@dataclass(frozen=True)
class _Relation:
    view_names: frozenset[str]
    columns: frozenset[str]
    column_origins: dict[str, frozenset[str]] = field(default_factory=dict)
    project_unique: bool = False
    has_project_key: bool = False

    @property
    def view_name(self) -> str:
        return sorted(self.view_names)[0]


@dataclass(frozen=True)
class _Source:
    alias: str
    relation: _Relation


class SQLGuard:
    """Valida SQL gerado sem confiar em prefixos, regex ou texto do prompt."""

    def __init__(self, *, limits: GuardLimits = DEFAULT_GUARD_LIMITS) -> None:
        self.limits = limits

    def validate(self, sql: str) -> ValidatedSQL:
        reasons: list[str] = []
        if not isinstance(sql, str) or not sql.strip():
            raise SQLGuardError(reasons=("empty_sql",))
        if len(sql) > self.limits.max_sql_characters:
            reasons.append("sql_too_long")
        if sqlglot is None or exp is None:
            raise SQLGuardError("Parser SQL indisponível.", reasons=("parser_unavailable",))

        try:
            statements = sqlglot.parse(sql, read="postgres")
        except Exception as exc:
            raise SQLGuardError("SQL não pôde ser analisado.", reasons=("parse_error",)) from exc

        if len(statements) != 1:
            reasons.append("multiple_statements")
            raise SQLGuardError(reasons=reasons)

        statement = statements[0]
        if not isinstance(statement, exp.Select):
            reasons.append("root_not_select")
        self._scan_forbidden_nodes(statement, reasons)
        self._scan_complexity(statement, reasons)
        if reasons:
            raise SQLGuardError(reasons=reasons)

        cte_relations: dict[str, _Relation] = {}
        physical_views: set[str] = set()
        for cte in self._cte_definitions(statement):
            cte_name = self._identifier_name(cte.alias_or_name).lower()
            if not cte_name or "." in cte_name:
                reasons.append("cte_name_not_allowed")
                continue
            if getattr(cte, "alias_column_names", None):
                reasons.append("cte_column_aliases_not_allowed")
                continue
            body = cte.this
            if isinstance(body, exp.Subquery):
                body = body.this
            if not isinstance(body, exp.Select):
                reasons.append("cte_not_select")
                continue
            relation = self._validate_select(body, cte_relations, physical_views, reasons)
            if relation is not None:
                cte_relations[cte_name] = relation

        if not reasons:
            self._validate_select(statement, cte_relations, physical_views, reasons)

        if not physical_views:
            reasons.append("no_physical_gold_view")
        if not physical_views.issubset(ALLOWED_VIEWS):
            reasons.append("view_not_allowlisted")
        if reasons:
            raise SQLGuardError(reasons=reasons)
        ordered_views = tuple(sorted(physical_views))
        return ValidatedSQL(
            sql=sql.strip(),
            statement=statement,
            view_name=ordered_views[0],
            view_names=ordered_views,
        )

    def check(self, sql: str) -> tuple[bool, list[str]]:
        """Retorna resultado estruturado para integrações que não usam exceções."""

        try:
            self.validate(sql)
        except SQLGuardError as exc:
            return False, list(exc.reasons)
        return True, []

    def _scan_forbidden_nodes(self, statement: Any, reasons: list[str]) -> None:
        for node in statement.walk():
            node_name = type(node).__name__
            if node_name in _FORBIDDEN_NODE_NAMES:
                reasons.append("forbidden_statement")
            if node_name in _TABLE_FUNCTION_NODE_NAMES:
                reasons.append("table_function")
            if node_name in _SET_OPERATION_NAMES:
                reasons.append("set_operation")
            if node_name in _PARAMETER_NODE_NAMES:
                reasons.append("parameter_not_allowed")
            if isinstance(node, exp.Subquery):
                reasons.append("subquery_not_allowed")
            if isinstance(node, exp.Lateral):
                reasons.append("lateral")
            if isinstance(node, exp.Star):
                reasons.append("wildcard")
            if isinstance(node, exp.Lock):
                reasons.append("lock")
            if isinstance(node, exp.Into):
                reasons.append("select_into")
            if isinstance(node, exp.Func) and not isinstance(node, exp.Binary):
                function_name = node.sql_name().upper()
                if function_name not in ALLOWED_FUNCTIONS:
                    reasons.append("function_not_allowlisted")

        for select in statement.find_all(exp.Select):
            if select.args.get("locks"):
                reasons.append("lock")
            if select.args.get("into"):
                reasons.append("select_into")
            with_node = select.args.get("with_")
            if with_node is not None and with_node.args.get("recursive"):
                reasons.append("recursive_cte")
        for join in statement.find_all(exp.Join):
            if str(join.args.get("kind") or "").upper() == "CROSS":
                reasons.append("cross_join")

    def _scan_complexity(self, statement: Any, reasons: list[str]) -> None:
        nodes = list(statement.walk())
        if len(nodes) > self.limits.max_ast_nodes:
            reasons.append("ast_node_limit")
        if self._depth(statement) > self.limits.max_ast_depth:
            reasons.append("ast_depth_limit")
        cte_count = sum(1 for node in nodes if isinstance(node, exp.CTE))
        if cte_count > self.limits.max_ctes:
            reasons.append("cte_limit")
        subquery_count = sum(1 for node in nodes if isinstance(node, exp.Subquery))
        if subquery_count > self.limits.max_subqueries:
            reasons.append("subquery_limit")
        if sum(1 for node in nodes if isinstance(node, exp.Join)) > self.limits.max_joins:
            reasons.append("join_limit")
        if sum(1 for node in nodes if isinstance(node, exp.AggFunc)) > self.limits.max_aggregations:
            reasons.append("aggregation_limit")

    def _cte_definitions(self, statement: Any) -> list[Any]:
        with_node = statement.args.get("with_")
        return list(with_node.expressions) if with_node is not None else []

    def _validate_select(
        self,
        select: Any,
        cte_relations: dict[str, _Relation],
        physical_views: set[str],
        reasons: list[str],
    ) -> _Relation | None:
        from_node = select.args.get("from_")
        if from_node is None or from_node.this is None:
            reasons.append("select_without_source")
            return None
        if from_node.expressions:
            reasons.append("multiple_sources")
            return None
        source = from_node.this
        if not isinstance(source, exp.Table):
            reasons.append("source_not_table")
            return None
        base_relation = self._resolve_relation(source, cte_relations, physical_views, reasons)
        if base_relation is None:
            return None

        aliases: dict[str, _Source] = {}
        self._register_source(source, base_relation, aliases, reasons)
        relation_list = [base_relation]
        combined_relation = base_relation
        for join in select.args.get("joins") or []:
            joined_table = join.this
            if not isinstance(joined_table, exp.Table):
                reasons.append("join_source_not_table")
                continue
            joined_relation = self._resolve_relation(
                joined_table,
                cte_relations,
                physical_views,
                reasons,
            )
            if joined_relation is None:
                continue
            self._register_source(joined_table, joined_relation, aliases, reasons)
            relation_list.append(joined_relation)
            self._validate_join(
                join,
                aliases,
                combined_relation,
                joined_relation,
                relation_list,
                reasons,
            )
            combined_relation = self._join_relation(combined_relation, joined_relation)

        if len(relation_list) > self.limits.max_relations:
            reasons.append("relation_limit")
        self._validate_columns(select, aliases, reasons)
        self._validate_semantics(select, aliases, relation_list, reasons)
        return self._select_relation(select, aliases, relation_list)

    def _register_source(
        self,
        table: Any,
        relation: _Relation,
        aliases: dict[str, _Source],
        reasons: list[str],
    ) -> None:
        alias = self._identifier_name(table.alias_or_name).lower()
        if not alias:
            reasons.append("source_without_alias")
            return
        if alias in aliases:
            reasons.append("duplicate_source_alias")
            return
        aliases[alias] = _Source(alias=alias, relation=relation)

    def _validate_join(
        self,
        join: Any,
        aliases: dict[str, _Source],
        combined_relation: _Relation,
        joined_relation: _Relation,
        relation_list: list[_Relation],
        reasons: list[str],
    ) -> None:
        side = str(join.args.get("side") or "").upper()
        if side in _UNSAFE_JOIN_SIDES:
            reasons.append("join_type_not_allowlisted")
        if str(join.args.get("kind") or "").upper() == "CROSS":
            reasons.append("cross_join")
        predicate = join.args.get("on")
        if not isinstance(predicate, exp.EQ):
            reasons.append("join")
            reasons.append("join_predicate_not_allowlisted")
            return
        if any(
            isinstance(node, exp.Or | exp.And | exp.Func | exp.Cast)
            for node in predicate.walk()
        ):
            reasons.append("join")
            reasons.append("join_predicate_not_allowlisted")
            return
        left, right = predicate.left, predicate.right
        if not isinstance(left, exp.Column) or not isinstance(right, exp.Column):
            reasons.append("join")
            reasons.append("join_predicate_not_allowlisted")
            return
        if left.name.lower() != "project_id" or right.name.lower() != "project_id":
            reasons.append("join")
            reasons.append("join_key_not_allowlisted")
            return
        left_source = aliases.get(self._identifier_name(left.table).lower())
        right_source = aliases.get(self._identifier_name(right.table).lower())
        if left_source is None or right_source is None or left_source is right_source:
            reasons.append("join")
            reasons.append("join_key_not_allowlisted")
            return
        if not left_source.relation.has_project_key or not right_source.relation.has_project_key:
            reasons.append("join")
            reasons.append("join_key_not_allowlisted")
            return
        if not combined_relation.project_unique and not joined_relation.project_unique:
            reasons.append("join")
            reasons.append("join_fanout_requires_preaggregation")
        if len(relation_list) > self.limits.max_relations:
            reasons.append("relation_limit")

    @staticmethod
    def _join_relation(left: _Relation, right: _Relation) -> _Relation:
        return _Relation(
            view_names=left.view_names | right.view_names,
            columns=left.columns | right.columns,
            column_origins={**left.column_origins, **right.column_origins},
            project_unique=left.project_unique and right.project_unique,
            has_project_key=left.has_project_key and right.has_project_key,
        )

    def _resolve_relation(
        self,
        table: Any,
        cte_relations: dict[str, _Relation],
        physical_views: set[str],
        reasons: list[str],
    ) -> _Relation | None:
        table_name = self._identifier_name(table.name).lower()
        if not table.args.get("db") and table_name in cte_relations:
            return cte_relations[table_name]
        if table.args.get("catalog") or (
            table.args.get("db") and self._identifier_name(table.db).lower() != "gold"
        ):
            reasons.append("schema_not_allowlisted")
        if not table.args.get("db"):
            reasons.append("schema_not_allowlisted")
            return None
        view_name = f"gold.{table_name}"
        physical_views.add(view_name)
        if view_name not in ALLOWED_VIEWS:
            reasons.append("view_not_allowlisted")
            return None
        contract = _CATALOG_BY_VIEW[view_name]
        columns = GENERATABLE_COLUMNS[view_name]
        origins = {column: frozenset({view_name}) for column in columns}
        return _Relation(
            view_names=frozenset({view_name}),
            columns=columns,
            column_origins=origins,
            project_unique=contract.grain in {
                "uma linha por projeto",
                "uma linha por projeto no snapshot atual",
            },
            has_project_key="project_id" in columns,
        )

    def _validate_columns(
        self,
        select: Any,
        aliases: dict[str, _Source],
        reasons: list[str],
    ) -> None:
        select_aliases = self._select_aliases(select)
        for column in self._direct_find(select, exp.Column):
            column_name = self._identifier_name(column.name).lower()
            qualifier = self._identifier_name(column.table).lower()
            if column.args.get("db") or column.args.get("catalog"):
                reasons.append("column_qualification_not_allowed")
                continue
            if qualifier:
                source = aliases.get(qualifier)
                if source is None or column_name not in source.relation.columns:
                    reasons.append("column_not_allowlisted")
                continue
            matches = [
                source
                for source in aliases.values()
                if column_name in source.relation.columns
            ]
            if len(matches) > 1:
                if column_name not in select_aliases:
                    reasons.append("ambiguous_column")
            elif not matches and column_name not in select_aliases:
                reasons.append("column_not_allowlisted")

    def _validate_semantics(
        self,
        select: Any,
        aliases: dict[str, _Source],
        relation_list: list[_Relation],
        reasons: list[str],
    ) -> None:
        has_non_unique_join = len(relation_list) > 1 and any(
            not relation.project_unique for relation in relation_list
        )
        for function in self._direct_find(select, exp.Func):
            function_name = function.sql_name().upper()
            if function_name == "COUNT":
                argument = function.this
                if not isinstance(argument, exp.Distinct) or len(argument.expressions) != 1:
                    reasons.append("count_must_distinct_project_id")
                    reasons.append("count_must_distinct_key")
                    continue
                count_column = argument.expressions[0]
                if (
                    not isinstance(count_column, exp.Column)
                    or count_column.name.lower() not in _COUNT_KEYS
                ):
                    reasons.append("count_must_distinct_project_id")
                    reasons.append("count_must_distinct_key")
            if function_name in _FINANCIAL_FUNCTIONS:
                if isinstance(function.this, exp.Distinct):
                    reasons.append("distinct_financial_aggregation")
                for column in function.find_all(exp.Column):
                    source = self._column_source(column, aliases)
                    if source is None:
                        continue
                    if (
                        column.name.lower() == "planned_investment_amount"
                        and "gold.vw_project_location_current" in source.relation.view_names
                    ):
                        reasons.append("financial_aggregation_on_location")
                    if has_non_unique_join and source.relation.project_unique:
                        reasons.append("financial_aggregation_after_fanout")

    def _column_source(self, column: Any, aliases: dict[str, _Source]) -> _Source | None:
        qualifier = self._identifier_name(column.table).lower()
        if qualifier:
            return aliases.get(qualifier)
        matches = [
            source
            for source in aliases.values()
            if column.name.lower() in source.relation.columns
        ]
        return matches[0] if len(matches) == 1 else None

    def _select_relation(
        self,
        select: Any,
        aliases: dict[str, _Source],
        relation_list: list[_Relation],
    ) -> _Relation:
        columns: set[str] = set()
        origins: dict[str, frozenset[str]] = {}
        for expression in select.expressions:
            output_name = self._expression_output_name(expression)
            if not output_name:
                continue
            output_name = output_name.lower()
            columns.add(output_name)
            origins[output_name] = self._expression_origins(expression, aliases)
        project_unique = len(relation_list) == 1 and relation_list[0].project_unique
        project_unique = project_unique or self._groups_by_project_id(select)
        project_unique = project_unique or self._selects_distinct_project_id(select)
        return _Relation(
            view_names=frozenset().union(*(relation.view_names for relation in relation_list)),
            columns=frozenset(columns),
            column_origins=origins,
            project_unique=project_unique,
            has_project_key="project_id" in columns,
        )

    def _expression_origins(self, expression: Any, aliases: dict[str, _Source]) -> frozenset[str]:
        origins: set[str] = set()
        for column in expression.find_all(exp.Column):
            source = self._column_source(column, aliases)
            if source is not None:
                origins.update(
                    source.relation.column_origins.get(
                        column.name.lower(), source.relation.view_names
                    )
                )
        return frozenset(origins)

    @staticmethod
    def _expression_output_name(expression: Any) -> str:
        if isinstance(expression, exp.Alias):
            return expression.alias_or_name
        if isinstance(expression, exp.Column):
            return expression.name
        return expression.output_name

    def _groups_by_project_id(self, select: Any) -> bool:
        group = select.args.get("group")
        if group is None:
            return False
        return any(
            isinstance(column, exp.Column) and column.name.lower() == "project_id"
            for column in group.expressions
        )

    @staticmethod
    def _selects_distinct_project_id(select: Any) -> bool:
        if select.args.get("distinct") is None or len(select.expressions) != 1:
            return False
        expression = select.expressions[0]
        if isinstance(expression, exp.Alias):
            expression = expression.this
        return isinstance(expression, exp.Column) and expression.name.lower() == "project_id"

    def _select_aliases(self, select: Any) -> frozenset[str]:
        return frozenset(
            expression.alias_or_name.lower()
            for expression in select.expressions
            if isinstance(expression, exp.Alias) and expression.alias_or_name
        )

    def _direct_find(self, root: Any, node_type: Any) -> Iterable[Any]:
        stack = list(root.iter_expressions())
        while stack:
            node = stack.pop()
            if isinstance(node, exp.Select | exp.Subquery | exp.CTE):
                continue
            if isinstance(node, node_type):
                yield node
            stack.extend(node.iter_expressions())

    @staticmethod
    def _depth(root: Any) -> int:
        def visit(node: Any, depth: int) -> int:
            children = list(node.iter_expressions())
            if not children:
                return depth
            return max(visit(child, depth + 1) for child in children)

        return visit(root, 1)

    @staticmethod
    def _identifier_name(value: Any) -> str:
        if value is None:
            return ""
        return str(getattr(value, "name", value) or "")


def validate_sql(sql: str, *, limits: GuardLimits = DEFAULT_GUARD_LIMITS) -> ValidatedSQL:
    """Valida uma consulta e retorna o envelope que pode ser injetado no executor."""

    return SQLGuard(limits=limits).validate(sql)


def check_sql(sql: str, *, limits: GuardLimits = DEFAULT_GUARD_LIMITS) -> tuple[bool, list[str]]:
    return SQLGuard(limits=limits).check(sql)


validate = validate_sql
