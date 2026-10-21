/* Visuals use the same executed SQL report CSVs as the report explorer. */
const usd=v=>Number(v).toLocaleString('en-US',{style:'currency',currency:'USD'});
const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function reportRows(name){const response=await fetch(`data/reports/${name}.csv`);if(!response.ok)throw Error(`Report unavailable: ${name}`);return parseCsv(await response.text()).rows;}
function bars(rows,label,value,extra=()=>'',color='teal'){
 const max=Math.max(...rows.map(value),1);
 return rows.map(r=>`<div class="bar-row"><div class="bar-label"><span>${safe(label(r))}</span><b>${usd(value(r))}</b></div><div class="track"><div class="fill ${color}" style="width:${100*value(r)/max}%"></div></div><small>${safe(extra(r))}</small></div>`).join('');
}
async function drawDashboard(){
 const [months,products,segments,customers]=await Promise.all(['q1_monthly_revenue','q2_top_products','q3_segment_channel','q4_customer_rank'].map(reportRows));
 const byMonth=new Map(months.map(r=>[r[0],Number(r[1])]));
 const values=Array.from({length:12},(_,i)=>byMonth.get(`2024-${String(i+1).padStart(2,'0')}`)||0),max=Math.max(...values);
 document.querySelector('#monthly-chart').innerHTML=`<div class="columns">${values.map((v,i)=>`<div class="column"><span>${usd(v)}</span><div class="column-track"><div style="height:${100*v/max}%" title="${usd(v)}"></div></div><small>${new Date(2024,i,1).toLocaleString('en-US',{month:'short'})}</small></div>`).join('')}</div>`;
 document.querySelector('#product-chart').innerHTML=bars(products,r=>r[0],r=>Number(r[1]),r=>`${r[2]}% of delivered revenue`);
 document.querySelector('#segment-chart').innerHTML=bars(segments,r=>`${r[0]} · ${r[1]}`,r=>Number(r[2]),()=>'', 'blue');
 document.querySelector('#customer-chart').innerHTML=bars(customers,r=>`#${r[3]}  ${r[0]}`,r=>Number(r[2]),r=>`${r[1]} delivered order${r[1]==1?'':'s'}`,'blue');
 const response=await fetch('data/orders.csv');if(!response.ok)throw Error('Orders unavailable');
 const orders=parseCsv(await response.text());const status=orders.headers.indexOf('status');const delivered=orders.rows.filter(r=>r[status]==='Delivered').length;
 const factResponse=await fetch('data/fact_sales.csv');if(!factResponse.ok)throw Error('Fact data unavailable');const fact=parseCsv(await factResponse.text());const si=fact.headers.indexOf('status'),ri=fact.headers.indexOf('line_revenue_usd');const total=fact.rows.filter(r=>r[si]==='Delivered').reduce((sum,r)=>sum+Number(r[ri]),0);
 document.querySelector('#order-summary').textContent=`${delivered} delivered · ${orders.rows.length} source orders · ${fact.rows.length} source lines`;
 document.querySelector('#metrics').innerHTML=`<div class="card"><span>Delivered revenue</span><strong>${usd(total)}</strong><small>USD · excludes shipping</small></div><div class="card"><span>Delivered orders</span><strong>${delivered}</strong><small>Returned, cancelled and processing excluded</small></div><div class="card"><span>Average delivered order</span><strong>${usd(total/delivered)}</strong><small>Revenue ÷ distinct delivered orders</small></div>`;
}
drawDashboard().catch(e=>{document.querySelector('#dashboard-error').textContent=e.message;});
