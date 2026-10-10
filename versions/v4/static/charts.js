// Google Charts displays only aggregate counts. Names and free-text answers stay in HTML.
const SurveyCharts = (() => {
  const palette=['#315bb7','#159b89','#ef9a32','#9661ba','#dc6379','#4ba6c7','#8b9d3c','#bb7849'];
  let ready=false,failed=false;
  const tasks=new Set();
  function status(text){const n=document.getElementById('chartStatus');if(n)n.textContent=text;}
  function drawPie(task,data,options) {
    const values=task.values.filter(v=>v.count>0);
    const width=Math.min(task.container.clientWidth,840);
    const diameter=Math.min(300,Math.max(90,width*0.4)),radius=diameter/2;
    const labelWidth=Math.max(36,(width-diameter)/2-26);
    const fontSize=width<500?12:14;
    const measure=document.createElement('canvas').getContext('2d');
    measure.font=`bold ${fontSize}px Arial`;
    function wrap(label){
      const lines=[];let current='';
      for(const character of label){if(current && measure.measureText(current+character).width>labelWidth){lines.push(current);current=character;}else current+=character;}
      if(current)lines.push(current);return lines;
    }
    const total=values.reduce((sum,v)=>sum+v.count,0);let angle=0;
    const entries=values.map((value,index)=>{
      const mid=angle+Math.PI*value.count/total;angle+=2*Math.PI*value.count/total;
      const lines=wrap(value.label);
      return {index,mid,side:Math.sin(mid)>=0?1:-1,lines,height:lines.length*(fontSize+4),color:palette[index%palette.length]};
    });
    const groups=[entries.filter(e=>e.side<0),entries.filter(e=>e.side>0)];
    const height=Math.max(360,...groups.map(group=>group.reduce((sum,e)=>sum+e.height+8,32)));
    const cx=width/2,cy=height/2;
    const host=document.createElement('div');host.style.cssText=`position:relative;width:${width}px;height:${height}px;margin:0 auto;`;
    const canvas=document.createElement('div');host.append(canvas);task.container.replaceChildren(host);
    options.width=width;options.height=height;options.is3D=true;options.legend={position:'none'};
    options.chartArea={left:cx-radius,top:cy-radius,width:diameter,height:diameter};
    options.pieSliceTextStyle.fontSize=width<500?11:14;
    const chart=new google.visualization.PieChart(canvas);
    google.visualization.events.addListener(chart,'ready',()=>{
      const ns='http://www.w3.org/2000/svg';
      const svg=document.createElementNS(ns,'svg');svg.setAttribute('width',width);svg.setAttribute('height',height);svg.setAttribute('aria-hidden','true');
      svg.classList.add('pie-label-overlay');svg.style.cssText='position:absolute;inset:0;pointer-events:none;overflow:visible;';
      function shape(tag,attrs){const element=document.createElementNS(ns,tag);for(const [key,value] of Object.entries(attrs))element.setAttribute(key,value);return element;}
      // Use the rendered 3D ellipse, so connectors touch the visible slice rim.
      const surface=[...canvas.querySelectorAll('svg path')].find(path=>path.getAttribute('fill')===palette[0] && /A/.test(path.getAttribute('d')||''));
      const geometry=surface?.getAttribute('d').match(/^M([\d.-]+),([\d.-]+).*?A([\d.-]+),([\d.-]+),/);
      const pieX=geometry?Number(geometry[1]):cx;
      const pieY=geometry?Number(geometry[2]):cy-radius*0.1;
      const rx=geometry?Number(geometry[3]):radius;
      const ry=geometry?Number(geometry[4]):radius*0.8;
      const depth=Math.max(0,2*(cy-pieY));

      for(const group of groups){
        group.forEach(e=>{e.x=pieX+rx*Math.sin(e.mid);e.y=pieY-ry*Math.cos(e.mid)+(Math.cos(e.mid)<0?depth:0);e.top=e.y+(e.y<pieY?-18:18)-e.height/2;});
        group.sort((a,b)=>a.y-b.y);
        let bottom=12;for(const e of group){e.top=Math.max(e.top,bottom);bottom=e.top+e.height+8;}
        let next=height-12;for(const e of [...group].reverse()){e.top=Math.min(e.top,next-e.height);next=e.top-8;}
        for(const e of group){
          const textX=cx+e.side*(radius+18),labelY=e.top+e.height/2;
          const elbowX=textX-e.side*10;
          const line=shape('polyline',{points:`${e.x},${e.y} ${elbowX},${e.y} ${elbowX},${labelY} ${textX-e.side*5},${labelY}`,fill:'none',stroke:e.color,'stroke-width':1.4,'stroke-linejoin':'round'});line.classList.add('pie-connector');svg.append(line);
          svg.append(shape('circle',{cx:e.x,cy:e.y,r:2,fill:e.color}));
          const label=shape('text',{x:textX,y:e.top+fontSize,'text-anchor':e.side>0?'start':'end','font-family':'Arial','font-size':fontSize,'font-weight':'700',fill:'#26364b'});
          label.classList.add('pie-legend-label');
          e.lines.forEach((line,index)=>{const span=shape('tspan',{x:textX,dy:index?fontSize+4:0});span.textContent=line;label.append(span);});svg.append(label);
        }
      }
      host.append(svg);task.container.dataset.drawn='true';
    });
    chart.draw(data,options);
  }
  function draw(task) {
    if(!task.container.isConnected){tasks.delete(task);return;}
    if(!ready || !task.container.getClientRects().length || !task.container.clientWidth)return;
    try {
      const data=new google.visualization.DataTable(); data.addColumn('string','항목'); data.addColumn('number','응답 수');
      const options={height:360,fontName:'Arial',colors:palette,backgroundColor:'transparent',chartArea:{left:55,top:20,width:'75%',height:'65%'},legend:{position:task.kind==='pie'?'right':'none'},hAxis:{slantedText:true,slantedTextAngle:25},vAxis:{minValue:0,format:'0'},tooltip:{isHtml:false}};
      if(task.kind==='pie') {
        data.addRows(task.values.filter(v=>v.count>0).map(v=>[v.label,v.count])); options.pieSliceText='percentage'; options.pieSliceTextStyle={color:'#ffffff',fontSize:14,bold:true}; options.sliceVisibilityThreshold=0;
        drawPie(task,data,options);
      } else {
        data.addColumn({type:'string',role:'style'}); data.addColumn({type:'string',role:'annotation'});
        data.addRows(task.values.map((v,i)=>[v.label,v.count,`color: ${palette[i%palette.length]}`,`${v.count}`]));
        new google.visualization.ColumnChart(task.container).draw(data,options);
      }
      if(task.kind!=='pie')task.container.dataset.drawn='true';
    }catch(e){task.container.textContent='차트를 표시하지 못했습니다. 아래 표에서 응답 수를 확인하세요.';}
  }
  function redraw(){for(const task of tasks)draw(task);}
  function render(parent,title,values,percent=false,kind='column',multiple=false){
    const section=document.createElement('section');section.className='chart-section';
    const heading=document.createElement('h3');heading.textContent=title;section.append(heading);
    if(!values.some(v=>v.count>0)){const empty=document.createElement('p');empty.textContent='응답 없음';section.append(empty);parent.append(section);return;}
    if(multiple){const hint=document.createElement('p');hint.className='hint';hint.textContent='표의 비율은 전체 응답자 대비입니다. 파이의 크기는 전체 선택 횟수 대비이며, 복수 선택으로 표의 비율 합계는 100%를 넘을 수 있습니다.';section.append(hint);}
    const chart=document.createElement('div');chart.className='google-chart';chart.setAttribute('aria-label',title);chart.setAttribute('role','img');chart.textContent=failed?'차트 연결 실패 · 아래 표에서 확인하세요.':'차트 준비 중...';section.append(chart);
    const table=document.createElement('table');table.className='chart-data'; const head=document.createElement('tr');['항목','응답 수',...(percent?['비율']:[])].forEach(t=>{const th=document.createElement('th');th.textContent=t;head.append(th);});table.append(head);
    values.forEach(v=>{const tr=document.createElement('tr');[v.label,`${v.count}건`,...(percent?[`${v.percent}%`]:[])].forEach(t=>{const td=document.createElement('td');td.textContent=t;tr.append(td);});table.append(tr);});
    section.append(table);parent.append(section);const task={container:chart,values,kind};tasks.add(task);draw(task);
  }
  const script=document.createElement('script');script.src='https://www.gstatic.com/charts/loader.js';script.async=true;
  script.onload=()=>{google.charts.load('current',{packages:['corechart'],language:'ko',safeMode:true}).then(()=>{ready=true;status('');redraw();});};
  script.onerror=()=>{failed=true;status('Google Charts 연결에 실패했습니다. 아래 표로 응답 수를 확인할 수 있습니다.');for(const t of tasks)t.container.textContent='차트 연결 실패 · 아래 표에서 확인하세요.';};
  document.head.append(script);setTimeout(()=>{if(!ready)status('차트 로딩이 지연되고 있습니다. 아래 표에서 응답 수를 확인할 수 있습니다.');},10000);
  let timer;window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(redraw,150);});document.addEventListener('toggle',redraw,true);
  return {render,redraw};
})();
