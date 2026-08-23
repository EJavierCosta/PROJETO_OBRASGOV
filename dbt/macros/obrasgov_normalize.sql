{% macro obrasgov_normalize(value) -%}
nullif(regexp_replace(lower(trim({{ value }}::text)), '\s+', ' ', 'g'), '')
{%- endmacro %}

{% macro obrasgov_organization_key(cnpj, name) -%}
md5(
    case
        when regexp_replace(coalesce({{ cnpj }}::text, ''), '\D', '', 'g') ~ '^\d{14}$'
            then 'cnpj||' || regexp_replace({{ cnpj }}::text, '\D', '', 'g')
        else 'name||' || coalesce({{ obrasgov_normalize(name) }}, '∅')
    end
)
{%- endmacro %}
