/* 固定焦点场景共用网页时钟与确定性导出，只请求本地导入图片。 */
(async () => {
  const read=async path=>{const response=await fetch(path);if(!response.ok)throw Error('无法读取 '+path+'，请用本地服务打开');return response.json();};
  try {
    const [catalog,plan,inventory]=await Promise.all([read('data/catalog.json'),read('data/timeline.json'),read('assets/inventory.json')]);
    const byId=new Map(catalog.models.map(e=>[e.id,e])),entries=catalog.journeyIds.map(id=>byId.get(id)),images=new Map();
    await Promise.all(entries.filter(e=>inventory[e.id]).map(e=>new Promise(resolve=>{
      const image=new Image();image.onload=()=>{images.set(e.id,image);resolve();};image.onerror=resolve;image.src=inventory[e.id];
    })));
    window.FOCUS_DATA={entries,timeline:plan};window.FOCUS_CONFIG={images};
    const paint=await FocusJourney.prepare(),range=document.getElementById('seek'),button=document.getElementById('play');
    const settings=window.RenderSettings||{start:0,duration:plan.duration};let time=0;
    const stamp=t=>String(Math.floor(t/60)).padStart(2,'0')+':'+String(Math.floor(t%60)).padStart(2,'0');
    function draw(value){
      time=Math.max(0,Math.min(plan.duration,value));paint(time);range.value=time;
      document.getElementById('time').value=stamp(time)+' / '+stamp(plan.duration);
      window.JourneyPreview={time,loadedImages:images.size,total:entries.length,ready:true,character:'独立程序化人物'};
    }
    const missing=entries.length-images.size;range.max=plan.duration;range.step=1/plan.fps;
    document.getElementById('notice').textContent=missing?'缺少'+missing+'份真实图片。当前用于预览布局；导入图片后再生成影片。':'已加载全部'+entries.length+'份影像。可播放、按章节或机型定位。';
    for(const chapter of plan.chapters){const b=document.createElement('button');b.textContent=chapter.number+' · '+chapter.title;b.onclick=()=>draw(chapter.start);document.getElementById('chapters').append(b);}
    entries.forEach((entry,i)=>{const option=document.createElement('option');option.value=i;option.textContent=entry.release.displayLabel+' · '+entry.name;document.getElementById('model').append(option);});
    document.getElementById('model').onchange=e=>draw(plan.entries[Number(e.target.value)].arrival);
    range.oninput=()=>draw(Number(range.value));button.disabled=false;
    if(window.JourneyPlayer)JourneyPlayer.init({draw,getTime:()=>time,duration:plan.duration,button});
    if(window.gsap){
      const clock={t:0},timeline=gsap.timeline({paused:true});
      timeline.to(clock,{t:settings.duration,duration:settings.duration,ease:'none',onUpdate:()=>draw(settings.start+clock.t)},0);
      window.__timelines=window.__timelines||{};window.__timelines['phone-journey']=timeline;window.__hfForceTimelineRebind?.();
    }
    draw(settings.start);
  }catch(error){document.getElementById('notice').textContent=error.message;window.JourneyPreview={ready:false,error:error.message};}
})();
