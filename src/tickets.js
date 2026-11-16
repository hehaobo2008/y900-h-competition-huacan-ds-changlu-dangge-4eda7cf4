import {railwayTicket} from './rail_ticket.js';
import {objectTicket,objectRatios} from './object_tickets.js';

// One DOM object moves from an unobtrusive ticket face to a readable reverse.
export function createTicketView({letters,zones,onFlip,onClose,onDrag,onDragStart,onSwipe,onLaunch}){
  const get=id=>document.getElementById(id),root=get('ticketLayer'),rotor=get('ticketRotor');
  let index=0,back=false,visible=false,ignoreClick=false,press=null;
  function layout(){
    if(!visible)return;
    const limit=Math.max(130,innerHeight-36-get('ticketTools').offsetHeight-get('ticketLaunchActions').offsetHeight-get('ticketFlipHint').offsetHeight);
    const rail=!!letters[index].rail;
    const faceHeight=root.clientWidth*(rail?390/620:objectRatios[letters[index].kind]);
    const height=back?Math.min(get('ticketBackContent').scrollHeight+2,limit):Math.min(faceHeight,limit);
    rotor.style.height=height+'px';
  }
  const observer=new ResizeObserver(layout);observer.observe(get('ticketBackContent'));
  addEventListener('resize',layout);
  function flip(){
    if(!visible||back)return;
    onFlip(index);
  }
  get('ticketFront').addEventListener('click',e=>{if(ignoreClick){e.preventDefault();ignoreClick=false;return}flip()});
  get('ticketFront').addEventListener('pointerdown',e=>{
    if(e.pointerType==='mouse')return;
    ignoreClick=false;press={id:e.pointerId,x:e.clientX,y:e.clientY,previousY:e.clientY,dragged:false};
  });
  get('ticketFront').addEventListener('pointermove',e=>{
    if(!press||e.pointerId!==press.id)return;
    if(!press.dragged&&Math.hypot(e.clientX-press.x,e.clientY-press.y)>9){press.dragged=true;onDragStart()}
    if(press.dragged){onDrag((press.previousY-e.clientY)*.034);press.previousY=e.clientY;}
  });
  get('ticketFront').addEventListener('pointerup',e=>{
    if(!press||e.pointerId!==press.id)return;
    const tapped=!press.dragged,swipe=press.y-e.clientY;press=null;ignoreClick=true;
    // Complete touch taps here and suppress a second compatibility click.
    if(tapped){e.preventDefault();flip();}
    // Let the touch sequence finish before making its target inert.
    if(!tapped&&swipe>40)requestAnimationFrame(()=>onSwipe(swipe*.034));
    setTimeout(()=>ignoreClick=false,500);
  });
  get('ticketFront').addEventListener('pointercancel',()=>{press=null;ignoreClick=true;setTimeout(()=>ignoreClick=false,500)});
  get('shelveTicket').addEventListener('click',onClose);
  get('cardClose').addEventListener('click',onClose);
  get('launchBtn').addEventListener('click',()=>onLaunch(false));
  get('skipFinale').addEventListener('click',()=>onLaunch(true));
  get('wishInput').addEventListener('focus',()=>requestAnimationFrame(()=>{
    if(visible&&back)get('wishInput').scrollIntoView({block:'center',inline:'nearest'});
  }));
  return {
    show(idx,{reading=false,archive=false,stop=false,canLaunch=false}={}){
      index=idx;visible=true;back=reading;
      const letter=letters[idx],zone=zones[idx];
      root.dataset.kind=letter.kind;root.dataset.archive=String(archive);root.dataset.stop=String(stop);
      get('objectTicketFace').hidden=!!letter.rail;
      get('objectTicketFace').innerHTML=letter.rail?'':objectTicket(letter.kind);
      get('railTicketFace').hidden=!letter.rail;
      get('railTicketFace').innerHTML=letter.rail?railwayTicket(letter.rail,idx===3):'';
      get('ticketYear').textContent=zone.year+' · '+zone.label;
      get('ticketLabel').textContent=letter.frontLabel;
      get('ticketText').textContent=letter.frontText;
      get('ticketDistance').textContent=letter.distance;
      get('ticketSerial').textContent='SH / 0'+(idx+1);
      get('ticketStub').textContent=idx===0?'家藏':'存根';
      get('cardEyebrow').textContent=zone.year+' · '+letter.distance;
      get('cardTitle').textContent=letter.backText;
      get('cardBody').textContent=letter.body;
      get('ticketBackLabel').textContent=letter.backLabel;
      get('ticketReverseBrand').textContent=['灶边字条','东街电影院 · 票背留字','铁路旅客运输 · K1986','铁路旅客运输 · G2023','星河港 / 登船牌 · 航行留言'][idx];
      get('cardIndex').textContent=String(idx+1).padStart(2,'0')+' / 05';
      get('ticketFront').setAttribute('aria-label',letter.frontLabel+'，'+letter.distance+'。轻点翻面阅读');
      get('ticketComposer').hidden=idx!==4;
      get('keepLetter').hidden=idx===4;
      get('ticketLaunchActions').hidden=!canLaunch;
      get('cardClose').hidden=canLaunch;
      root.classList.add('show');root.inert=false;
      get('ticketBack').scrollTop=0;
      this.setSide(reading);layout();
      root.classList.remove('arriving');
      if(stop&&!reading){void root.offsetWidth;root.classList.add('arriving');}
    },
    setSide(value){
      back=!!value;root.dataset.side=back?'back':'front';
      get('ticketFlipHint').hidden=false;
      get('ticketFlipHint').textContent=root.dataset.archive==='true'
        ?(back?'读完收起，回到旅程':'轻点翻到背面')
        :(back?'票外向前滑动，继续游览':'轻点翻到背面 · 再向前滑动，继续游览');
      get('ticketFront').inert=back;get('ticketBack').inert=!back;
      get('ticketFront').setAttribute('aria-expanded',String(back));
      get('ticketFront').setAttribute('aria-hidden',String(back));get('ticketBack').setAttribute('aria-hidden',String(!back));
      get('shelveTicket').textContent=back?'收起，继续游览':'收好，继续游览';
      layout();
    },
    hide(){visible=false;root.classList.remove('show','arriving');root.inert=true;root.removeAttribute('aria-modal');root.setAttribute('role','group');press=null;},
    layout,
    get visible(){return visible},
    get back(){return back},
    get index(){return index}
  };
}
