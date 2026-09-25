# Superset API payload skeletons

## Dataset
```http
GET  /api/v1/dataset/<id>                       → result.sql, result.columns[], result.database.id
POST /api/v1/dataset/  {"database":<DB_ID>,"schema":"<schema>","table_name":"<name>","sql":"<select…>"}
PUT  /api/v1/dataset/<id>  {"sql":"<select…>"}                                 # same output columns
PUT  /api/v1/dataset/<id>/refresh                                              # re-read columns from SQL
PUT  /api/v1/dataset/<id>?override_columns=true {"sql":"…","columns":[{"column_name":"Block"},…]}  # explicit alternative
```

## Chart (table example)
```json
{"slice_name":"<name>","viz_type":"table","datasource_id":<DATASET_ID>,"datasource_type":"table",
 "params":"{\"all_columns\":[\"Block\",\"Village\"],\"row_limit\":10000,\"query_mode\":\"raw\"}",
 "query_context":"{\"datasource\":{\"id\":<DATASET_ID>,\"type\":\"table\"},\"queries\":[{\"columns\":[\"Block\",\"Village\"],\"row_limit\":10000}],\"result_format\":\"json\",\"result_type\":\"full\"}"}
```
`params` and `query_context` are **JSON strings**. Big number: `viz_type:"big_number_total"`, `metric`. Bar: `echarts_timeseries_bar`.

## Link chart → dashboard
`PUT /api/v1/chart/<id> {"dashboards":[<DASH_ID>]}`, then add it to the dashboard's `position_json` for layout.

## Native filter entry (append to json_metadata.native_filter_configuration)
```json
{"id":"NATIVE_FILTER-<hex>","name":"Block","filterType":"filter_select",
 "targets":[{"datasetId":<DATASET_ID>,"column":{"name":"Block"}}],
 "controlValues":{"multiSelect":true,"enableEmptyFilter":false},
 "chartsInScope":[<CHART_IDS>],"scope":{"rootPath":["ROOT_ID"],"excluded":[]},
 "cascadeParentIds":[],"defaultDataMask":{"filterState":{}},"type":"NATIVE_FILTER"}
```
For a cascade (District → Block), set the child's `cascadeParentIds:["NATIVE_FILTER-<district>"]`.

## SQL Lab execute (verification)
`POST /api/v1/sqllab/execute/ {"database_id":<DB_ID>,"sql":"…","schema":null,"runAsync":false,"json":true}`

## Find what uses a dataset
`GET /api/v1/chart/?q=(filters:!((col:datasource_id,opr:eq,value:<DATASET_ID>)))`, then `GET /api/v1/chart/<id>` → `dashboards[]`.
