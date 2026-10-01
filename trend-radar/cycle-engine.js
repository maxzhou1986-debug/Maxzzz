/* Cycle rules v1: observable daily structures, not a calibrated probability model. */
(function(g){
'use strict';
const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
const high=a=>Math.max(...a.map(b=>b.h)), low=a=>Math.min(...a.map(b=>b.l));
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function analyze(d={},now=Date.now(),cached=false){
 const base={stage:'数据不足',type:'待判断',label:'暂停信号',code:'WAIT',cl:'amber',reasons:[],missing:[],sell:'未触发结构卖点',invalid:'尚无有效交易结构',support:null,resistance:null};
 const raw=d.bars||[];
 if(d.error||raw.length<30||raw.some((b,i)=>![b.t,b.o,b.h,b.l,b.c].every(Number.isFinite)||b.c<=0||b.l<=0||b.h<b.l||b.h<Math.max(b.o,b.c)||b.l>Math.min(b.o,b.c)||(i&&b.t<=raw[i-1].t)))return {...base,missing:['需要至少30根连续有效日K']};
 // Use source session end to exclude the unfinished daily candle. Unknown sessions are conservative.
 const end=d.sessionEnd, start=d.sessionStart, qt=d.quoteTime;
 const trusted=Number.isFinite(end)&&Number.isFinite(start)&&Number.isFinite(qt);
 let bars=raw.slice();
 if(!trusted||(now<end*1000&&bars.at(-1).t>=start))bars.pop();
 if(bars.length<30)return {...base,missing:['完整日K不足30根']};
 const last=bars.at(-1),prev=bars.at(-2),prior=bars.slice(-21,-1),recent=bars.slice(-6,-1),older=bars.slice(-11,-6);
 const support=low(recent),resistance=high(prior),m20=mean(bars.slice(-20).map(b=>b.c));
 const rising=low(recent)>low(older)&&high(recent)>high(older);
 const falling=low(recent)<low(older)&&high(recent)<high(older);
 const near=last.l<=support*1.025&&last.c>=support;
 const hold=near&&last.c>prev.c&&last.l>=support&&last.c>=last.l+(last.h-last.l)*.6;
 let r={...base,support,resistance,asOf:last.t,stage:rising?'趋势延续':falling?'退潮下跌':'止跌观察',type:rising?'趋势回踩型':'底部反转观察',label:'观察',reasons:[rising?'近期高点与低点均抬高':falling?'近期高点与低点均下移':'尚无连续抬高的高低点结构'],missing:['等待结构突破或回踩验证'],invalid:'收盘跌破支撑 '+support.toFixed(2)};
 // Breakout must be followed by TWO completed daily closes above a fixed, pre-breakout level.
 let event=null;
 for(let i=bars.length-1;i>=Math.max(20,bars.length-6);i--){const level=high(bars.slice(i-20,i));if(bars[i].c>level*1.005){event={i,level};break;}}
 if(event){const after=bars.slice(event.i+1),held=after.length>=2&&after.every(b=>b.c>event.level)&&low(after)>=event.level*.99;
  if(after.every(b=>b.c>event.level))Object.assign(r,{stage:held?'上升确认':'初步转强',code:'B2',label:held?'B2已确认（日线结构）':'B2刚触发',cl:held?'green':'amber',resistance:event.level,invalid:'收盘跌回突破位 '+event.level.toFixed(2),reasons:['收盘突破此前20日高点',held?'随后至少两根完整日K守住突破位':'突破后的守稳时间不足'],missing:held?['仍需核对大盘与板块环境']:['等待后续至少两根完整日K守住']});
 }else if(near){Object.assign(r,{code:'B1',label:hold?'B1承接（日线）':'B1进入支撑区',cl:hold&&rising?'green':'amber',reasons:r.reasons.concat(hold?'下探支撑后收回，收盘高于前日':'进入前5日低点附近'),missing:[rising?'盘中承接尚未验证':'下跌或震荡中的止跌试探，趋势尚未确认']});}
 const broken=last.c<support*.99&&prev.c<low(bars.slice(-7,-2))*.99;
 const vol=last.v>0&&prior.every(b=>b.v>0)?last.v/mean(prior.map(b=>b.v)):null;
 if(broken){Object.assign(r,{stage:'转弱',code:'S2',label:'结构破坏',cl:'red',sell:'趋势退出观察',reasons:['连续两根完整日K跌破各自此前5日低点'],missing:['等待收复破位区域'],invalid:'原支撑已破坏；具体交易失效须对应实际入场计划'});}
 else if(last.c/m20>1.12&&vol!==null&&vol>=1.5&&last.c<=prev.c){Object.assign(r,{stage:'高位分歧',code:'S1',label:'止盈观察',cl:'amber',sell:'高乖离后放量滞涨',reasons:['距20日均线超过12%，放量但收盘未再上涨'],missing:['观察能否恢复上涨，尚不等于见顶']});}
 r.missing.push('情绪：缺少经验证的独立预期数据');
 const badTime=!trusted||qt*1000>now+60000||now-qt*1000>72*3600000;
 if(cached||badTime){r.historicalLabel=r.label;r.label='暂停信号';r.code='WAIT';r.cl='amber';r.missing.unshift(cached?'正在使用缓存，仅供历史复盘':!trusted?'缺少行情时间或交易时段，无法确认数据新鲜度':'行情时间异常或超过72小时，等待更新');r.sell='仅显示历史结构，暂停新卖点';}
 else if(now>=start*1000&&now<end*1000&&now-qt*1000>120000){r.historicalLabel=r.label;r.label='暂停盘中信号';r.code='WAIT';r.cl='amber';r.missing.unshift('行情延迟超过2分钟；以下仅为已完成日K结构');r.sell='仅供日线复盘';}
 return r;
}
function tuple(r){return[r.code,r.label,r.reasons.concat(r.missing).join('；'),r.cl];}
function render(r){if(!r)return '';return '<div class="cyclePanel"><b>周期：'+esc(r.stage)+' · '+esc(r.type)+'</b><p><span class="pill '+r.cl+'">'+esc(r.label)+'</span></p><p>依据：'+esc(r.reasons.join('；')||'数据不足')+'</p><p>待确认：'+esc(r.missing.join('；'))+'</p><p>卖点：'+esc(r.sell)+'</p><p>失效：'+esc(r.invalid)+'</p><small>日K截至 '+(r.asOf?new Date(r.asOf*1000).toISOString().slice(0,10):'未知')+' · 参数规则v1，未作胜率校准</small></div>';}
function watchStatus(r){
 if(!r||r.label.includes('暂停')||r.stage==='数据不足')return '数据待核验';
 if(['退潮下跌','转弱','高位分歧'].includes(r.stage))return '暂不观察';
 if(['初步转强','上升确认','趋势延续'].includes(r.stage))return '保留观察';
 if(r.stage==='止跌观察'&&r.label==='B1承接（日线）')return '保留观察';
 return '暂不观察';
}
const api={analyze,tuple,render,watchStatus};g.CycleEngine=api;if(typeof module!=='undefined')module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:this);
