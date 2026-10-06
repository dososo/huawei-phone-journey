/* 本地网页播放与可寻址渲染共用一套时间线，不请求远程手机图。 */
(async () => {
  const read = async path => {
    const response=await fetch(path);
    if(!response.ok)throw new Error('无法读取 '+path+'，请用本地服务打开');
    return response.json();
  };
  try {
    const [catalog,plan,inventory]=await Promise.all([read('data/catalog.json'),read('data/timeline.json'),read('assets/inventory.json')]);
    window.FullData=catalog;window.CompactData=plan;
    const byId=new Map(catalog.models.map(e=>[e.id,e])),entries=catalog.journeyIds.map(id=>byId.get(id)),images=new Map();
    await Promise.all(entries.filter(e=>inventory[e.id]).map(e=>new Promise(resolve=>{
      const image=new Image();image.onload=()=>{images.set(e.id,image);resolve();};image.onerror=resolve;image.src=inventory[e.id];
    })));
    await document.fonts.ready;
    const ctx=document.getElementById('film').getContext('2d'),range=document.getElementById('seek'),button=document.getElementById('play'),settings=window.RenderSettings||{start:0,duration:plan.duration};
    let time=0;
    const stamp=t=>String(Math.floor(t/60)).padStart(2,'0')+':'+String(Math.floor(t%60)).padStart(2,'0');
    function draw(value) {
      time=Math.max(0,Math.min(plan.duration,value));
      CompactJourney.draw(ctx,time,entries,images);
      const segment=CompactJourney.segmentAt(time),chapter=plan.chapters[segment.chapterIndex];
      ctx.save();ctx.font='28px 长卷宋体, serif';
      if(segment.kind==='chapter'){
        const elapsed=time-segment.start,slide=elapsed<.24?1920*(1-elapsed/.24):elapsed>segment.duration-.48?-1920*((elapsed-segment.duration+.48)/.48):0;
        ctx.translate(slide,0);ctx.fillStyle='#f2f0e9';ctx.fillRect(0,0,1920,1080);
        ctx.fillStyle='#b04b47';ctx.font='32px 长卷宋体, serif';ctx.fillText('第'+chapter.number+'章 · '+chapter.title.split('：')[0],143,270);
        ctx.fillStyle='#292b30';ctx.font='96px 长卷宋体, serif';ctx.fillText(chapter.title.split('：')[1],140,446);
        ctx.fillStyle='#716e69';ctx.font='30px 长卷宋体, serif';ctx.fillText(chapter.era+' · 华为手机设计游历',145,555);
        ctx.fillStyle='#b04b47';ctx.fillRect(144,603,770,2);
      } else if(segment.kind==='ending'){
        ctx.fillStyle='#f2f0e9';ctx.fillRect(0,0,1920,1080);ctx.fillStyle='#b04b47';ctx.fillText('九章 · 设计游历',145,292);
        ctx.fillStyle='#292b30';ctx.font='78px 长卷宋体, serif';ctx.fillText('你用过的那一款，在哪一年？',145,480);
        ctx.fillStyle='#716e69';ctx.font='28px 长卷宋体, serif';ctx.fillText('2004—2026 · 451份机型影像',145,590);
      } else if(chapter){
        ctx.fillStyle='#716e69';ctx.font='29px 长卷宋体, serif';ctx.textAlign='right';ctx.fillText(chapter.title,1830,52);
      }
      if(chapter){
        const progress=Math.max(0,Math.min(1,(time-chapter.journeyStart)/(chapter.end-chapter.journeyStart)));
        for(let i=0;i<9;i++){ctx.fillStyle='#d7d3cb';ctx.fillRect(1610+i*26,76,19,3);ctx.fillStyle='#b04b47';ctx.fillRect(1610+i*26,76,19*(i<chapter.index?1:i===chapter.index?progress:0),3);}
      }
      ctx.restore();range.value=time;document.getElementById('time').value=stamp(time)+' / '+stamp(plan.duration);
      window.JourneyPreview={time,loadedImages:images.size,total:entries.length,ready:true};
    }
    const missing=entries.length-images.size;
    document.getElementById('notice').textContent=missing?'缺少'+missing+'份真实图片。可先预览动画结构；导入图片后再生成影片。':'已加载全部451份真实影像。拖动进度条或选择章节、机型观看。';
    for(const c of plan.chapters){const b=document.createElement('button');b.textContent=c.number+' · '+c.title;b.onclick=()=>draw(c.start);document.getElementById('chapters').append(b);}
    entries.forEach((e,i)=>{const option=document.createElement('option');option.value=i;option.textContent=e.release.displayLabel+' · '+e.name;document.getElementById('model').append(option);});
    document.getElementById('model').onchange=e=>draw(plan.entries[Number(e.target.value)].arrival);
    range.oninput=()=>draw(Number(range.value));button.disabled=false;
    if(window.JourneyPlayer)JourneyPlayer.init({draw,getTime:()=>time,duration:plan.duration,button});
    if(window.gsap){
      const clock={t:0},timeline=gsap.timeline({paused:true});
      timeline.to(clock,{t:settings.duration,duration:settings.duration,ease:'none',onUpdate:()=>draw(settings.start+clock.t)},0);
      window.__timelines=window.__timelines||{};window.__timelines['phone-journey']=timeline;
    }
    draw(settings.start);
  } catch(error) {
    document.getElementById('notice').textContent=error.message;
    window.JourneyPreview={ready:false,error:error.message};
  }
})();
