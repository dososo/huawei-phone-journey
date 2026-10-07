/* 原画板与有界缓存；缺图明确显示，保留三款重点画板特例。 */
(() => {
  const C=540,cache=new Map();
  function panel(entry,image){
    const key=entry.id+entry.image.path;if(cache.has(key))return cache.get(key);
    const canvas=document.createElement('canvas');canvas.width=canvas.height=C;
    const c=canvas.getContext('2d'),style=entry.style,baseline=style.baseline;
    c.fillStyle=baseline==='P30 Pro'?'#242873':baseline==='P50 Pro'?'#a8946e':baseline==='P60 Pro'?'#e7e3df':style.background;c.fillRect(0,0,C,C);
    if(!image){
      c.fillStyle='#d7cec1';c.font='28px sans-serif';c.textAlign='center';
      c.fillText('未导入真实图片',C/2,C/2);
    }else if(baseline){
      const n=['P30 Pro','P50 Pro','P60 Pro'].indexOf(baseline),crop=[[280,760,390,680],[320,530,230,400],[180,440,215,450]][n];
      c.save();c.globalAlpha=[.58,.66,.62][n];c.drawImage(image,...crop,0,0,C,C);c.restore();
      c.fillStyle=['rgba(15,25,71,.44)','rgba(242,230,205,.32)','rgba(249,247,242,.34)'][n];c.fillRect(0,0,C,C);
      if(n===0)c.drawImage(image,(C-700/1500*496)/2,22,700/1500*496,496);
      if(n===1){const h=498,w=602/1312*h;c.drawImage(image,(C-w)/2,19,w,h);}
      if(n===2){const z=.486;c.drawImage(image,C/2-264*z,16,918*z,1106*z);}
    }else{
      const ratio=Math.min(498/image.height,492/image.width,entry.image.displayLimitPx/(1.5*Math.max(image.width,image.height))),w=image.width*ratio,h=image.height*ratio;
      c.drawImage(image,(C-w)/2,(C-h)/2,w,h);
    }
    c.strokeStyle=baseline==='P30 Pro'?'rgba(190,224,255,.28)':'rgba(93,83,75,.16)';c.lineWidth=1;c.strokeRect(.5,.5,C-1,C-1);
    if(cache.size>=8)cache.delete(cache.keys().next().value);cache.set(key,canvas);return canvas;
  }
  window.FullJourney={panel,clear:()=>cache.clear()};
})();
