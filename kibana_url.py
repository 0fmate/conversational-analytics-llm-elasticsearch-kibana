from urllib.parse import quote

def build_kibana_url(host, dashboard_id, filters=None, from_date="2025-02-28", to_date="2025-03-24"):
    base = f"{host}/app/dashboards#/view/{dashboard_id}"
    time_filter = f"_g=(time:(from:'{from_date}',to:'{to_date}'))"

    if filters:
        query_parts = []
        for field, value, op in filters:
            if op == "=":
                query_parts.append(f"{field}:{value}")
            else:
                query_parts.append(f"{field}:{op}{value}")
        full_query = " AND ".join(query_parts)
        encoded_query = quote(full_query, safe='')
        query_filter = f"_a=(index:'ds_tesi',filters:!(),query:(query_string:(analyze_wildcard:!t,query:'{encoded_query}')))"
    else:
        query_filter = f"_a=(index:'ds_tesi',filters:!(),query:(query_string:(analyze_wildcard:!t,query:'*')))"

    return f"{base}?{time_filter}&{query_filter}"
