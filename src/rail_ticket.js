// Drawn from the information hierarchy of the 12306 soft-paper and magnetic
// ticket specimens. Stations, services, dates and passenger data belong to the story.
const xml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
function matrix(seed){
  let cells='';
  for(let y=0;y<29;y++)for(let x=0;x<29;x++){
    const finder=[[0,0],[22,0],[0,22]].find(([a,b])=>x>=a&&x<a+7&&y>=b&&y<b+7);
    let ink;
    if(finder){const dx=x-finder[0],dy=y-finder[1];ink=dx===0||dx===6||dy===0||dy===6||(dx>=2&&dx<=4&&dy>=2&&dy<=4)}
    else if((x<8&&y<8)||(x>20&&y<8)||(x<8&&y>20))ink=false;
    else {seed=(Math.imul(seed,1664525)+1013904223)>>>0;ink=(seed>>>29)%2===0}
    if(ink)cells+='<rect x="'+x+'" y="'+y+'" width="1" height="1"/>';
  }
  return '<g transform="translate(495 250) scale(3.45)" fill="#222825">'+cells+'</g>';
}
export function railwayTicket(data,express=false){
  const text=(x,y,size,value,extra='')=>'<text x="'+x+'" y="'+y+'" font-size="'+size+'" '+extra+'>'+xml(value)+'</text>';
  const pink='#d08080',blue='#82acb6',ink=express?blue:pink;
  const wave=express?'M0 4L4 0M0 12L12 0M0 20L20 0M4 24L24 4M12 24L24 12M20 24L24 20':'M-4 1Q2 7 8 1T20 1T32 1M-4 7Q2 13 8 7T20 7T32 7M-4 13Q2 19 8 13T20 13T32 13M-4 19Q2 25 8 19T20 19T32 19';
  const watermark=express?'<g fill="#408ba0" opacity=".10"><path d="M120 221L415 174Q451 175 478 211L571 234 565 248 147 247Z"/><path d="M181 208L421 190 439 202 179 224Z" fill="#eaf5f4"/><path d="M208 226L215 225 215 240 208 240M235 224L242 223 242 240 235 240M262 222L269 221 269 240 262 240M289 220L296 219 296 240 289 240"/></g>':'<g fill="none" stroke="#a75858" opacity=".08"><ellipse cx="310" cy="195" rx="180" ry="112"/><ellipse cx="310" cy="195" rx="165" ry="101"/><path d="M146 198Q310 98 475 198Q310 298 146 198Z"/></g>';
  return '<svg viewBox="0 0 620 390" style="stroke:none;fill:none" xmlns="http://www.w3.org/2000/svg" focusable="false" role="presentation">'+
    '<defs><pattern id="ticketHatch" width="24" height="24" patternUnits="userSpaceOnUse"><path d="'+wave+'" fill="none" stroke="'+ink+'" stroke-width=".6" opacity=".25"/></pattern><linearGradient id="ticketStock" x2="0.15" y2="1"><stop stop-color="'+(express?'#d8e9e8':'#f2d6cf')+'"/><stop offset="1" stop-color="'+(express?'#b7d9df':'#eec6bf')+'"/></linearGradient></defs>'+
    '<rect width="620" height="390" rx="'+(express?12:1)+'" fill="'+(express?'#c9e0e2':'#f6f0e5')+'"/>'+
    '<rect x="'+(express?0:12)+'" y="'+(express?0:12)+'" width="'+(express?620:596)+'" height="'+(express?390:366)+'" rx="'+(express?12:0)+'" fill="url(#ticketStock)"/>'+
    '<rect x="12" y="12" width="596" height="354" fill="url(#ticketHatch)"/>'+watermark+
    (express?'<path d="M0 359H620V378Q620 390 608 390H12Q0 390 0 378Z" fill="#79b7c7" opacity=".65"/>':'<path d="M308 12L309 378" stroke="#b17265" stroke-opacity=".12"/>')+
    '<g fill="#212727" font-family="SimSun,STSong,serif" font-weight="400">'+
    text(28,48,27,data.serial,'fill="#bd555a" font-family="Courier New,monospace" letter-spacing="2"')+
    text(588,46,21,'检票口 '+data.gate,'text-anchor="end"')+
    text(34,105,34,data.from)+text(590,105,34,data.to,'text-anchor="end"')+
    text(310,101,29,data.service,'text-anchor="middle" font-family="Courier New,monospace"')+
    '<path d="M239 118H381L371 113M381 118L371 123" fill="none" stroke="#252b2b" stroke-width="1.3"/>'+
    text(35,135,17,data.fromRoman,'font-family="Courier New,monospace" letter-spacing="1"')+
    text(589,135,17,data.toRoman,'font-family="Courier New,monospace" text-anchor="end" letter-spacing="1"')+
    text(29,179,23,data.departure)+text(589,179,23,data.seat,'text-anchor="end"')+
    text(29,218,26,'￥'+data.fare+'元')+text(590,218,24,data.className,'text-anchor="end"')+
    text(314,216,21,express?'网':'学','text-anchor="middle"')+
    text(29,251,20,'限乘当日当次车')+
    text(30,288,22,'**** **** ****　宁宁')+
    '<rect x="43" y="306" width="416" height="44" fill="none" stroke="#38403d" stroke-width="1.2" stroke-dasharray="6 4"/>'+
    text(251,324,15,express?'报销凭证　遗失不补':'学生票　硬座','text-anchor="middle"')+
    text(251,343,15,'中国铁路祝您旅途愉快','text-anchor="middle"')+
    text(27,378,14,data.code,'font-family="Courier New,monospace" letter-spacing="1"')+
    text(588,378,15,data.from+'售','text-anchor="end"')+
    '</g>'+matrix(express?2023:2016)+'</svg>';
}
