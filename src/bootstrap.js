let sceneStarted=false,busy=false;
const loading=document.getElementById('loading');
const screen=document.getElementById('errorScreen');
async function open(){
  if(busy)return;
  busy=true;window.__error=null;
  screen.classList.add('hidden');screen.inert=true;
  loading.classList.remove('hidden');
  try{
    sceneStarted=true;
    await import('./main.js').then(module=>module.ready);
  }catch(error){
    console.error('Unable to open the scroll:',error);
    window.__error=error.message;
    loading.classList.add('hidden');
    screen.querySelector('p').textContent=error.assetTransfer
      ?'风景还没传完，已载入的部分会为你保留。点击下方继续展开。'
      :'画面暂时没能展开，请重新尝试。';
    screen.classList.remove('hidden');screen.inert=false;
    document.getElementById('retryBtn').focus();
  }finally{busy=false}
}
document.getElementById('retryBtn').addEventListener('click',()=>sceneStarted?location.reload():open());
open();
