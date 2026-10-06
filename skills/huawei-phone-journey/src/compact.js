/* 时间映射只改变推进速度；真实图片、共享骨架与空间材质绘法原样复用。 */
(() => {
  let openingCanvas;
  function segmentAt(t) {
    const segments=CompactData.segments;
    let lo=0,hi=segments.length-1;
    while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(segments[mid].start<=t)lo=mid;else hi=mid-1;}
    return segments[lo];
  }
  function sourceTime(t) {
    const s=segmentAt(t);
    if(s.kind==='ending')return FullData.timing.duration;
    if(s.kind==='chapter')return CompactData.entries[CompactData.chapters[s.chapterIndex].entryFirst].sourceStart;
    return s.sourceStart+(s.sourceEnd-s.sourceStart)*Math.max(0,Math.min(1,(t-s.start)/s.duration));
  }
  function draw(ctx,t,entries,images) {
    const s=segmentAt(t);
    let state;
    if(s.kind==='opening'){
      if(!openingCanvas){openingCanvas=document.createElement('canvas');openingCanvas.width=1920;openingCanvas.height=1080;}
      state=FullJourney.draw(openingCanvas.getContext('2d'),1920,1080,sourceTime(t),entries,images,FullData.timing);
      const phase=Math.max(0,Math.min(1,(t-s.start)/s.duration)),zoom=1.75+.15*phase;
      const cropWidth=1920/zoom,cropHeight=1080/zoom;
      ctx.drawImage(openingCanvas,800-cropWidth/2,490-cropHeight/2,cropWidth,cropHeight,0,0,1920,1080);
      ctx.fillStyle='#f2f0e9';ctx.fillRect(0,0,1920,96);
      ctx.fillStyle='#292b30';ctx.font='42px 长卷宋体';ctx.fillText('穿过华为手机的22年',86,63);
      ctx.fillStyle='#716e69';ctx.font='24px 长卷宋体';ctx.fillText('序幕 · 过界',1638,59);
    }else state=FullJourney.draw(ctx,1920,1080,sourceTime(t),entries,images,FullData.timing);
    return state;
  }
  window.CompactJourney={segmentAt,sourceTime,draw};
})();
