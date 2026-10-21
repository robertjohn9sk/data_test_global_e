"""Validate actual source-to-warehouse values; run pipeline.py first."""
import csv
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]

def main():
    raw = ROOT / 'data/raw/orders_raw.json'
    before = hashlib.sha256(raw.read_bytes()).hexdigest()
    source = json.loads(raw.read_text(), parse_float=Decimal)
    con = duckdb.connect(str(ROOT / 'data/warehouse/retail_bi.duckdb'), read_only=True)
    con.execute("SET TimeZone='UTC'")
    results = []
    def check(name, condition):
        results.append({'test': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)
    orders = source['orders']
    check('Metadata matches actual source orders', source['export_metadata']['record_count'] == len(orders) == 12)
    check('Order IDs are unique', len({o['order_id'] for o in orders}) == len(orders))
    check('All source orders loaded', con.execute('select count(*) from orders').fetchone()[0] == len(orders))
    expected_count = sum(len(o['line_items']) for o in orders)
    check('All source lines loaded without join loss or multiplication', con.execute('select count(*) from order_lines').fetchone()[0] == con.execute('select count(*) from fact_sales').fetchone()[0] == expected_count == 20)
    check('Fact natural key is unique', con.execute('select count(*) from (select order_id,line_number from fact_sales group by 1,2 having count(*)<>1)').fetchone()[0] == 0)
    expected_total = Decimal(0)
    for order in orders:
        loaded = con.execute('select status,channel,customer_id,currency,shipping_cost from orders where order_id=?',[order['order_id']]).fetchone()
        check('Order attributes: '+order['order_id'], loaded == (order['status'],order['channel'],order['customer']['customer_id'],order['currency'],Decimal(str(order['shipping_cost']))))
        for n,line in enumerate(order['line_items'],1):
            local = (Decimal(line['quantity'])*Decimal(str(line['unit_price']))*(1-Decimal(str(line.get('discount_pct') or 0))/100)).quantize(Decimal('.000001'),rounding=ROUND_HALF_UP)
            rate = {'USD':Decimal('1'),'EUR':Decimal('1.08')}[order['currency']]
            usd = (local*rate).quantize(Decimal('.000001'),rounding=ROUND_HALF_UP)
            actual=con.execute('select product_id,quantity,unit_price,discount_pct,currency,fx_rate_to_usd,line_revenue_local,line_revenue_usd,category_raw from order_lines where order_id=? and line_number=?',[order['order_id'],n]).fetchone()
            expected=(line['product_id'],line['quantity'],Decimal(str(line['unit_price'])),Decimal(str(line.get('discount_pct') or 0)),order['currency'],rate,local,usd,line['category'])
            check(f'Source line and independent revenue calculation: {order["order_id"]}/{n}',actual==expected)
            check(f'Fact revenue preserved: {order["order_id"]}/{n}',con.execute('select line_revenue_usd from fact_sales where order_id=? and line_number=?',[order['order_id'],n]).fetchone()[0]==usd)
            if order['status']=='Delivered': expected_total+=usd
    check('Delivered source total equals fact total and required checkpoint',expected_total==con.execute("select sum(line_revenue_usd) from fact_sales where status='Delivered'").fetchone()[0]==Decimal('9994.624060'))
    check('All non-delivered rows retained',con.execute("select count(*) from fact_sales where status<>'Delivered'").fetchone()[0]==5)
    check('No missing dimension references',con.execute('select count(*) from fact_sales f left join dim_customer c using(customer_key) left join dim_product p using(product_key) left join dim_date d using(date_key) where c.customer_key is null or p.product_key is null or d.date_key is null').fetchone()[0]==0)
    check('Sarah historical versions mapped correctly',con.execute("select f.order_id,c.customer_segment from fact_sales f join dim_customer c using(customer_key) where c.customer_id='CUST-1042' group by 1,2 order by 1").fetchall()==[('ORD-2024-001','Premium'),('ORD-2024-004','Premium'),('ORD-2024-012','VIP')])
    check('Category casing normalized',con.execute("select category from dim_product where product_id='PROD-416'").fetchone()[0]=='Home Appliances')
    check('Sports categories normalized',con.execute("select count(*) from dim_product where product_id in ('PROD-207','PROD-214') and category='Sports & Fitness'").fetchone()[0]==2)
    check('Flagged price retained',con.execute("select unit_price from order_lines where order_id='ORD-2024-009' and product_id='PROD-207'").fetchone()[0]==Decimal('149.99'))
    queries=[s for s in (ROOT/'sql/reporting_queries.sql').read_text().split(';') if s.strip()]
    for sql,path,count in zip(queries,sorted((ROOT/'data/output/reports').glob('*.csv')),[7,8,5,6]):
        rows=con.execute(sql).fetchall()
        with path.open() as f: expected=list(csv.reader(f))[1:]
        check('Standalone SQL matches CSV: '+path.name,[[str(v) for v in row] for row in rows]==expected and len(rows)==count)
    for path in (ROOT/'public/data').rglob('*.csv'):
        check('Website export matches warehouse export: '+path.name,path.read_bytes()==(ROOT/'data/output'/path.relative_to(ROOT/'public/data')).read_bytes())
    check('Raw source unchanged during validation',before==hashlib.sha256(raw.read_bytes()).hexdigest())
    con.close()
    output={'passed':len(results),'failed':0,'scope':'Supplied assessment dataset; not a general input-validation test suite.','tests':results}
    (ROOT/'docs/validation_results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(f'{len(results)} checks passed; see docs/validation_results.json')

if __name__=='__main__': main()
