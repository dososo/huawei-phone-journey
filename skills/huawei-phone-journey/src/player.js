/* 普通网页的播放时钟；导出工程不载入此模块。 */
window.JourneyPlayer={init({draw,getTime,duration,button}){
  let playing=false,last=0;
  button.onclick=()=>{playing=!playing;if(getTime()>=duration)draw(0);button.textContent=playing?'暂停':'播放';last=performance.now();};
  function tick(now){
    if(playing){draw(getTime()+(now-last)/1000);if(getTime()>=duration){playing=false;button.textContent='播放';}}
    last=now;requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}};
