/* 全集共用空间：真实图按比例展示，画板裁切同一飞行人，缓存限制在可见邻域。 */
(() => {
  const C=540,G=36,P=C+G,clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{x=clamp(x);return x*x*(3-2*x);},lerp=(a,b,x)=>a+(b-a)*x;
  const cache=new Map();
  function panel(entry,image){
    const key=entry.id+entry.image.path;if(cache.has(key))return cache.get(key);
    const canvas=document.createElement('canvas');canvas.width=canvas.height=C;
    const c=canvas.getContext('2d'),style=entry.style,baseline=style.baseline;
    c.fillStyle=baseline==='P30 Pro'?'#242873':baseline==='P50 Pro'?'#a8946e':baseline==='P60 Pro'?'#e7e3df':style.background;c.fillRect(0,0,C,C);
    const ratio=Math.min(498/image.height,492/image.width,entry.image.displayLimitPx/(1.5*Math.max(image.width,image.height))),w=image.width*ratio,h=image.height*ratio;
    c.drawImage(image,(C-w)/2,(C-h)/2,w,h);
    c.strokeStyle=baseline==='P30 Pro'?'rgba(190,224,255,.28)':'rgba(93,83,75,.16)';c.lineWidth=1;c.strokeRect(.5,.5,C-1,C-1);
    if(cache.size>=8)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
  }
  function state(t,count,timing){
    const {lead,step,duration,tail}=timing,tourEnd=lead+Math.max(0,count-1)*step;
    t=Math.max(0,Math.min(duration,t));
    const progress=Math.max(0,Math.min(count-1,(t-lead)/step)),last=Math.max(0,count-1);
    const leave=smooth((t-tourEnd-.45)/1.35),hero={x:210+progress*P+leave*60,y:270-leave*190,scale:.46,t};
    const zoomIn=smooth((t-1.15)/1.15),zoomOut=smooth((t-tourEnd-1.2)/Math.min(1.55,tail-1.2)),close=zoomIn*(1-zoomOut);
    const overview=zoomOut>0?Math.max(0,last-2)*P+846:846;
    return {hero,progress,index:Math.round(progress),close,cx:lerp(overview,hero.x+45,close),cy:lerp(294,270,close),z:lerp(.48,1,close),t};
  }
  function visible(state,count){
    const center=Math.floor(state.cx/P),radius=state.close<.5?4:3;
    return Array.from({length:radius*2+1},(_,i)=>center-radius+i).filter(i=>i>=0&&i<count);
  }
  function draw(c,w,h,t,entries,images,timing){
    const s=state(t,entries.length,timing),a=Math.floor(s.progress),b=Math.min(entries.length-1,a+1);
    s.hero.scale=lerp(entries[a].heroScale,entries[b].heroScale,smooth(s.progress-a));
    c.save();c.setTransform(1,0,0,1,0,0);c.fillStyle='#f2f0e9';c.fillRect(0,0,w,h);c.scale(w/1280,h/720);
    c.save();c.translate(lerp(880,550,s.close),lerp(335,331,s.close));c.scale(s.z,s.z);c.translate(-s.cx,-s.cy);
    const indices=visible(s,entries.length);
    for(const i of indices){
      const e=entries[i],image=images.get(e.id),x=i*P;
      c.save();c.shadowColor='rgba(19,23,31,.23)';c.shadowBlur=18;c.shadowOffsetY=8;if(image)c.drawImage(panel(e,image),x,0);else{c.fillStyle='#e9e5de';c.fillRect(x,0,C,C);c.fillStyle='#77736e';c.font='22px 长卷宋体';c.fillText('未导入真实图片',x+170,C/2);}c.restore();
      c.fillStyle='#b04b47';c.font='italic 20px 长卷宋体';c.fillText(String(i+1).padStart(2,'0'),x,578);
      c.fillStyle='#292b30';c.font='25px 长卷宋体';c.fillText(e.name,x+49,577,478);
      c.fillStyle='#716e69';c.font='17px 长卷宋体';c.fillText(e.release.displayLabel+' · '+(e.imageTier==='历史缩览'?'历史缩览':e.style.colorName),x+49,606,478);
    }
    PreviewHero.draw(c,{...s.hero,material:'draft'});
    for(const i of indices){
      const e=entries[i];if(!images.has(e.id))continue;
      c.save();c.beginPath();c.rect(i*P,0,C,C);c.clip();PreviewHero.draw(c,{...s.hero,material:e.style.kind,color:e.style.color});c.restore();
    }
    c.restore();
    if(s.close<1){
      const known=entries.map(e=>e.year).filter(Boolean);c.save();c.globalAlpha=1-s.close;
      if(t>timing.lead+(entries.length-1)*timing.step){c.fillStyle='#f2f0e9';c.fillRect(0,0,460,720);}
      c.fillStyle='#232b38';
      c.font='42px 长卷宋体';c.fillText('华为手机',58,284);c.fillText('风格游历',58,345);
      c.fillStyle='#77736e';c.font='17px 长卷宋体';c.fillText('真实产品图像 · 连续跨界',61,393);c.font='15px 长卷宋体';
      c.fillText(Math.min(...known)+' — '+Math.max(...known)+' · '+entries.length+'份影像',61,426);c.restore();
    }
    const current=entries[Math.min(entries.length-1,s.index)];
    if(current&&s.close>.95){c.fillStyle='#77736e';c.font='14px 长卷宋体';c.fillText(current.release.displayLabel+' / '+(s.index+1)+' · '+entries.length,58,36);}
    c.restore();return s;
  }
  window.FullJourney={draw,state,visible,panel,clear:()=>cache.clear(),cell:C,gap:G,pitch:P};
})();
