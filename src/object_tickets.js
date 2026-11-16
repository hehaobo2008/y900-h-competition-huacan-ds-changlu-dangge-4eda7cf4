// Three different objects, drawn in their own proportions and print languages.
// The railway tickets have their own period-specific renderer in rail_ticket.js.
const svg=(w,h,body)=>'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+w+' '+h+'" style="stroke:none;fill:none" aria-hidden="true">'+body+'</svg>';
function bars(x,y,width,height){
  let out='',at=0;
  for(let n=0;at<width;n++){const w=[2,1,3,1,2,4,1,1,3][n%9];out+='<rect x="'+(x+at)+'" y="'+y+'" width="'+Math.min(w,width-at)+'" height="'+height+'"/>';at+=w+([1,2,1,3,2][n%5]);}
  return out;
}
export const objectRatios={note:330/470,ticket:290/650,boarding:340/780};
export function objectTicket(kind){
  if(kind==='note')return svg(470,330,`
    <defs><linearGradient id="note-paper" x2=".8" y2="1"><stop stop-color="#fff4d7"/><stop offset="1" stop-color="#e4cf9f"/></linearGradient></defs>
    <path d="M8 6L57 4 89 7 135 5 170 7 211 4 259 7 307 4 350 7 413 5 462 46 464 99 461 142 465 190 461 227 464 272 462 321 420 325 376 321 332 324 286 321 238 326 192 322 151 325 105 322 58 325 7 320 9 271 6 225 9 177 5 130 8 79Z" fill="url(#note-paper)"/>
    <path d="M413 5L410 48 462 46Z" fill="#b69b6d" opacity=".32"/><path d="M413 5L416 41 462 46Z" fill="#f8e9c5"/>
    <path d="M231 7Q226 167 236 323" stroke="#b99d6c" opacity=".25"/><path d="M234 7Q229 167 239 323" stroke="#fff9e3" opacity=".7"/>
    <g stroke="#a99876" opacity=".2"><path d="M30 101L439 101M30 153L439 153M30 205L439 205M30 257L439 257"/></g>
    <g fill="#4c4d43" font-family="KaiTi,STKaiti,serif" transform="rotate(-2 220 156)">
      <text x="42" y="78" font-size="22">给放学的孩子：</text>
      <text x="60" y="145" font-size="35">饭温在灶上，</text>
      <text x="65" y="199" font-size="35">记得早点回家。</text>
      <text x="326" y="261" font-size="27">外婆</text>
      <text x="321" y="293" font-size="16" opacity=".72">一九八三 · 夏</text>
    </g>
    <path d="M49 302Q35 291 45 276" stroke="#ac8356" stroke-width="3" opacity=".12"/>
  `);
  if(kind==='ticket')return svg(650,290,`
    <defs><pattern id="cinema-fibre" width="6" height="6" patternUnits="userSpaceOnUse"><path d="M0 1L6 2" stroke="#8b3c33" stroke-width=".4" opacity=".08"/></pattern></defs>
    <path d="M7 3H493A11 11 0 0 0 515 3H643V287H515A11 11 0 0 0 493 287H7Z" fill="#f0ddba"/>
    <path d="M7 3H493A11 11 0 0 0 515 3H643V287H515A11 11 0 0 0 493 287H7Z" fill="url(#cinema-fibre)"/>
    <g fill="none" stroke="#9f4135"><path d="M20 17H490M519 17H630V273H519M490 273H20Z" stroke-width="1.5"/><path d="M25 23H483M523 23H624V267H523M483 267H25Z" stroke-width=".5"/><path d="M504 21V270" stroke-dasharray="3 5"/></g>
    <g font-family="SimSun,serif" fill="#943e34">
      <text x="254" y="56" text-anchor="middle" font-size="30" letter-spacing="7">东街电影院</text>
      <path d="M46 72H462" stroke="#943e34"/>
      <text x="254" y="112" text-anchor="middle" font-size="22" letter-spacing="9">电影入场券</text>
      <text x="54" y="155" font-size="20">一九九六年八月十六日</text>
      <text x="54" y="201" font-size="31">伍排　壹座</text>
      <text x="333" y="198" font-size="21">晚场 19:30</text>
      <path d="M46 221H462" stroke="#943e34" opacity=".6"/>
      <text x="54" y="248" font-size="16">票价　叁元整</text>
      <text x="331" y="248" font-size="15">凭券入场 · 对号入座</text>
      <text x="567" y="53" text-anchor="middle" font-size="18">副　券</text>
      <text x="567" y="103" text-anchor="middle" font-size="20">伍排</text>
      <text x="567" y="135" text-anchor="middle" font-size="20">壹座</text>
      <text x="567" y="184" text-anchor="middle" font-size="15">晚场 19:30</text>
      <text x="567" y="210" text-anchor="middle" font-size="14">入场撕验</text>
      <text x="567" y="246" text-anchor="middle" font-family="Courier New,monospace" font-size="16">No.018639</text>
    </g>
    <g transform="rotate(-12 419 143)" fill="none" stroke="#ab4b3a" opacity=".7"><ellipse cx="419" cy="145" rx="34" ry="26"/><text x="419" y="150" text-anchor="middle" fill="#ab4b3a" stroke="none" font-family="SimSun,serif" font-size="14">售票专用</text></g>
  `);
  if(kind==='boarding')return svg(780,340,`
    <defs><clipPath id="boarding-edge"><rect width="780" height="340" rx="14"/></clipPath></defs>
    <g clip-path="url(#boarding-edge)">
      <rect width="780" height="340" fill="#eff4f3"/>
      <path d="M0 0H780V66H0Z" fill="#112e40"/>
      <path d="M0 66H780V70H0Z" fill="#76b9b3"/>
      <path d="M587 70H780V340H587Z" fill="#dde9e8"/>
      <g fill="none" stroke="#83acae" opacity=".35"><ellipse cx="473" cy="179" rx="94" ry="65" transform="rotate(-35 473 179)"/><ellipse cx="473" cy="179" rx="62" ry="65"/><path d="M379 179H566M473 113V244"/></g>
      <g font-family="Microsoft YaHei,PingFang SC,sans-serif">
        <g fill="#e8f3f1"><text x="30" y="43" font-size="24" letter-spacing="3">星河港</text><text x="152" y="43" font-size="15" letter-spacing="2">XINGHE SPACEPORT</text><text x="747" y="41" text-anchor="end" font-size="19">登船牌 / BOARDING PASS</text></g>
        <g fill="#52717c" font-size="13" letter-spacing="1"><text x="30" y="103">出发 / ORIGIN</text><text x="324" y="103">抵达 / DESTINATION</text></g>
        <g fill="#173a4b" font-size="44" font-weight="500"><text x="28" y="152">地球</text><text x="322" y="152">星河</text></g>
        <g fill="#52717c" font-size="16" letter-spacing="2"><text x="31" y="178">EARTH</text><text x="325" y="178">XINGHE</text></g>
        <path d="M159 135H282M269 128L282 135 269 142" stroke="#568e95" stroke-width="2" fill="none"/>
        <g fill="#52717c" font-size="13"><text x="30" y="213">旅客 / PASSENGER</text><text x="241" y="213">航次 / VOYAGE</text><text x="418" y="213">登船时间 / BOARDING</text></g>
        <g fill="#173a4b" font-size="23"><text x="30" y="245">宁宁</text><text x="241" y="245" font-family="Consolas,monospace">SH 001</text><text x="418" y="245" font-family="Consolas,monospace">06:30</text></g>
        <path d="M30 264H553" stroke="#b8cccc"/>
        <g fill="#173a4b">${bars(31,281,235,31)}</g>
        <text x="292" y="300" fill="#52717c" font-family="Consolas,monospace" font-size="13">SH001 / EAR-XHE / 08A</text>
        <text x="292" y="319" fill="#52717c" font-size="11">家在地球 · 远行到星河</text>
        <g fill="#52717c" font-size="13"><text x="612" y="103">登船凭证</text><text x="612" y="166">舱门 / GATE</text><text x="612" y="242">座位 / SEAT</text></g>
        <text x="612" y="134" fill="#173a4b" font-size="21">宁宁</text><text x="752" y="134" text-anchor="end" fill="#52717c" font-size="12">NINGNING</text>
        <g fill="#173a4b" font-family="Consolas,monospace" font-size="36"><text x="612" y="207">03</text><text x="612" y="284">08A</text></g>
        <text x="612" y="319" fill="#52717c" font-size="12" letter-spacing="2">SH 001 · 星河航行</text>
      </g>
      <path d="M587 79V332" stroke="#8aa4ac" stroke-dasharray="4 5"/>
      <circle cx="587" cy="0" r="10" fill="#0a1c27"/><circle cx="587" cy="340" r="10" fill="#0a1c27"/>
    </g>
  `);
  return '';
}
