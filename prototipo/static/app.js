'use strict';
const el = id => document.getElementById(id);
const DAYS = ['','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'];
const state = {csrf: null, user: null, offerings: [], enrollments: []};

async function api(path, method='GET', data=null) {
  const headers = {};
  if (data !== null) headers['Content-Type'] = 'application/json';
  if (method !== 'GET' && state.csrf) headers['X-CSRF-Token'] = state.csrf;
  let response;
  try {response = await fetch(path, {method, credentials:'same-origin', headers, body:data === null ? null : JSON.stringify(data)});}
  catch (_) { throw new Error('No hay conexión con el servidor.'); }
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.message || `Error HTTP ${response.status}`);
  return payload;
}
function node(tag, text, className='') {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
}
function showToast(message, error=false) {
  const toast = el('toast');
  toast.textContent = message;
  toast.classList.toggle('error', error);
  toast.classList.remove('hidden');
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.add('hidden'), 5500);
}
function renderTableRows(target, records, render, emptyMessage) {
  target.replaceChildren();
  if (!records.length) {
    const tr = document.createElement('tr'); const td = node('td',emptyMessage);
    td.colSpan = 6; tr.append(td); target.append(tr); return;
  }
  records.forEach(record => target.append(render(record)));
}
function cell(tr, content) { const td=document.createElement('td'); if (typeof content === 'string') td.textContent=content; else td.append(content); tr.append(td); return td; }
function badge(text, kind='') { return node('span',text,`badge ${kind}`); }
function renderOfferings() {
  renderTableRows(el('offering-rows'),state.offerings,o => {
    const tr=document.createElement('tr');
    const title=document.createElement('div'); title.append(node('strong',o.name),node('small',o.course_id)); cell(tr,title);
    cell(tr,o.section); cell(tr,`${DAYS[o.day_of_week]} ${o.starts_at}–${o.ends_at}`);
    cell(tr,`${o.remaining} / ${o.capacity}`);
    cell(tr,badge(o.status==='CERRADA'?'Cerrada':o.remaining===0?'Sin cupos':'Abierta',o.status==='CERRADA'?'closed':o.remaining===0?'low':''));
    const button=node('button','Inscribir','action');button.type='button';button.disabled=o.status!=='ABIERTA'||o.remaining<1||state.user.role!=='ESTUDIANTE';
    button.addEventListener('click',()=>confirmEnrollment(o));cell(tr,button);
    return tr;
  },'No hay ofertas disponibles.');
}
function renderEnrollments() {
  renderTableRows(el('enrollment-rows'),state.enrollments,e=>{
    const tr=document.createElement('tr');cell(tr,e.course_id);cell(tr,e.name);
    cell(tr,`${DAYS[e.day_of_week]} ${e.starts_at}–${e.ends_at}`);
    cell(tr,badge(e.state));return tr;
  },state.user.role==='DOCENTE'?'No disponible para el rol docente.':'Todavía no tienes asignaturas inscritas.');
}
async function loadDashboard(){
  try {
    const offers=await api('/api/offerings');state.offerings=offers.offerings;
    if(state.user.role==='ESTUDIANTE') state.enrollments=(await api('/api/enrollments')).enrollments;
    else state.enrollments=[];
    el('stat-offerings').textContent=state.offerings.filter(o=>o.status==='ABIERTA'&&o.remaining>0).length;
    el('stat-enrollments').textContent=state.user.role==='ESTUDIANTE'?state.enrollments.length:'—';
    renderOfferings();renderEnrollments();
  } catch(e){showToast(e.message,true);}
}
function confirmEnrollment(o){
  el('confirm-title').textContent=`Inscribir ${o.course_id}`;
  el('confirm-desc').textContent=`Se validarán cupos, prerrequisitos, cruces de horario, duplicidad y el paz y salvo de SistemaContable antes de confirmar ${o.name}, grupo ${o.section}.`;
  const dialog=el('confirm-dialog');dialog.showModal();
  dialog.onclose=async()=>{
    if(dialog.returnValue!=='ok')return;
    const button=el('confirm-yes');button.disabled=true;
    try {const result=await api('/api/enroll','POST',{offering_id:o.id});showToast(`${result.enrollment.course}: matrícula confirmada. Cupo actualizado.`);}
    catch(e){showToast(e.message,true);}
    finally{button.disabled=false;await loadDashboard();}
  };
}
function renderSession(){
  const logged=!!state.user;
  el('login-view').classList.toggle('hidden',logged);
  el('dashboard').classList.toggle('hidden',!logged);
  el('logout').classList.toggle('hidden',!logged);
  el('user-chip').classList.toggle('hidden',!logged);
  if(!logged)return;
  el('user-chip').textContent=`${state.user.name} · ${state.user.role}`;
  el('welcome').textContent=`Bienvenido, ${state.user.name}. Solicitudes sujetas a validaciones de CU-02.`;
  el('teacher-notice').classList.toggle('hidden',state.user.role!=='DOCENTE');
  const finance=el('finance-chip'); finance.textContent=state.user.role==='DOCENTE'?'Acceso docente':state.user.finance.replaceAll('_',' ');
  finance.classList.toggle('bad',state.user.finance!=='PAZ_Y_SALVO'&&state.user.role==='ESTUDIANTE');
  loadDashboard();
}
async function init(){
  try {const info=await api('/api/session');if(info.authenticated){state.user=info.user;state.csrf=info.csrf;}} catch(e){showToast(e.message,true);}
  renderSession();
}
el('login-form').addEventListener('submit',async e=>{
  e.preventDefault();el('login-error').textContent='';el('login-submit').disabled=true;
  try {await api('/api/login','POST',{username:el('username').value,password:el('password').value});const info=await api('/api/session');state.user=info.user;state.csrf=info.csrf;renderSession();}
  catch(err){el('login-error').textContent=err.message;}
  finally{el('login-submit').disabled=false;}
});
el('logout').addEventListener('click',async()=>{
  try{await api('/api/logout','POST',{});state.user=null;state.csrf=null;renderSession();}
  catch(e){showToast(e.message,true);}
});
el('refresh').addEventListener('click',loadDashboard);
init();
