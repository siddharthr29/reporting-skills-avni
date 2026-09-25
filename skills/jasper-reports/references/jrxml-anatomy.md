# JRXML anatomy — the parts you edit

```xml
<jasperReport name="District_wise_details" ...>
  <parameter name="fiscal_year" class="java.lang.String"/>                 <!-- $P{fiscal_year} -->
  <parameter name="LoggedInUserAttribute_LocationFilter" class="java.lang.String" isForPrompting="false">
      <defaultValueExpression><![CDATA[""]]></defaultValueExpression>
  </parameter>
  <queryString><![CDATA[
      with work as ( select ... from rwb.<table> where is_voided = false and fy = $P{fiscal_year} )
      select district, sum(silt) as silt_total ...
      from work
      where 1 = 1 $P!{LoggedInUserAttribute_LocationFilter}              -- raw splice (RLS)
      group by district
  ]]></queryString>
  <field name="district"   class="java.lang.String"/>                      <!-- must match SQL output names -->
  <field name="silt_total" class="java.math.BigDecimal"/>
  <columnHeader> ... <textField><textFieldExpression><![CDATA["Silt total"]]></textFieldExpression></textField> ...
  <detail><band> ... <textField><textFieldExpression><![CDATA[$F{silt_total}]]></textFieldExpression></textField>
  <variable name="silt_sum" calculation="Sum"><variableExpression><![CDATA[$F{silt_total}]]></variableExpression></variable>
</jasperReport>
```

| Change | Touch |
|---|---|
| Fix logic / filter | `<queryString>` only |
| New data column | `<queryString>` + `<field>` + header `textField` + detail `textField` (+ `<variable>` if totalled) |
| Rename a header | header `textFieldExpression` |
| Drill to next level | hyperlink `<hyperlinkParameter>` passing `$F{district}` as the next report's parameter |

Rules:
- `$F{x}` names must exist as `<field>` elements **and** as SQL output columns (the case matters).
- Keep `class` types consistent (`BigDecimal` for sums, `String` for text). A mismatch fails at fill time.
- `$P!{}` is spliced raw, so never put user input there.
