(() => {
  const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{x=clamp(x);return x*x*(3-2*x);};
  async function prepare(){
    const config=window.FOCUS_CONFIG||{},data=window.FOCUS_DATA||{entries:window.MODELS,timeline:window.TIMELINE};
    const entries=config.sampleIds?config.sampleIds.map(id=>data.entries.find(e=>e.id===id)):data.entries;
    const timeline=config.sampleTimeline||data.timeline,rows=timeline.entries,chapters=timeline.chapters||[];
    const canvas=document.getElementById('film'),ctx=canvas.getContext('2d'),measure=document.createElement('canvas').getContext('2d');
    const byId=new Map(entries.map((e,i)=>[e.id,i]));
    const introIds=['U626','P30 Pro','Pocket 2'].map((name,k)=>{const i=entries.findIndex(e=>e.name===name);return i>=0?i:Math.round(k*(entries.length-1)/2);});
    const index=r=>byId.get(r.modelId||r.id),images=entries.map(e=>config.images?.get(e.id)||null);
    await document.fonts.ready;
    const transition=Math.max(.34,Math.min(.4,config.transitionDuration??.4)),lead=.04,half=(transition-lead)/2;
    const font=(n,w=600)=>`${w} ${n}px ${config.fontFamily||'sans-serif'}`,foreground='#eee9df',muted='#c6bcb0';
    const focusPlans={
      'honor-honor10xlite-33ff910d':{zoom:1.18,center:[.5,.5]},
      'huawei-mate50pro-5799fce5':{zoom:1.85,center:[.5,.5]},
      'huawei-nova11pro-02bba62c':{zoom:1.3,center:[.5,.553]},
      'huawei-mate60pro-a7477a18':{zoom:1.16,center:[.5,.5]},
      'huawei-mate90promaxcollector-40a63e19':{zoom:2.1,center:[.5,.495]},
      ...(config.focusPlans||{})
    };
    function state(t){
      t=Math.max(0,Math.min(timeline.duration,t));let lo=0,hi=rows.length-1;
      while(lo<hi){const m=Math.ceil((lo+hi)/2);if(rows[m].start<=t)lo=m;else hi=m-1;}
      const row=rows[lo],chapter=chapters.find(c=>c.index===row.chapterIndex);
      const card=chapters.find(c=>t>=c.cardStart&&t<c.cardEnd);
      const intro=t<(timeline.introEnd||0),outro=t>=(timeline.outroStart??timeline.duration);
      const cardRow=card?rows.find(r=>r.chapterIndex===card.index):null;
      const target=index(cardRow||row),first=chapter?rows.find(r=>r.chapterIndex===chapter.index)===row:lo===0;
      const travel=!card&&!intro&&!outro&&!first&&lo>0&&t<row.start+transition;
      const u=travel?clamp((t-row.start)/transition):1,switched=!travel||t>=row.start+lead+half;
      return {t,row,chapter:card||chapter,card,intro,outro,target,old:card?Math.max(0,target-1):travel?index(rows[lo-1]):target,main:switched?target:index(rows[lo-1]),travel,u,switched};
    }
    function nativeLong(e){return Math.max(...(e.nativeSize||[images[byId.get(e.id)]?.naturalWidth||212,images[byId.get(e.id)]?.naturalHeight||212]));}
    function mainSize(e){const n=nativeLong(e);return n<240?600:n<400?650:700;}
    function camera(s,e){
      const plan=focusPlans[e.id],length=s.row.duration-transition,age=s.t-s.row.start-transition;
      if(!plan||s.travel||s.card||s.intro||s.outro||length<1.4)return {zoom:1,center:[.5,.5],amount:0};
      const amount=smooth((age-.2)/.32)*(1-smooth((age-(length-.45))/.3));
      return {zoom:1+(plan.zoom-1)*amount,center:[.5+(plan.center[0]-.5)*amount,.5+(plan.center[1]-.5)*amount],amount};
    }
    function panel(p,cam){
      const e=entries[p.i],im=images[p.i],board=FullJourney.panel(e,im),rect=[p.x-p.size/2,p.y-p.size/2,p.x+p.size/2,p.y+p.size/2];
      ctx.save();ctx.shadowColor='rgba(0,0,0,.5)';ctx.shadowBlur=22;ctx.shadowOffsetY=10;
      ctx.drawImage(board,...rect.slice(0,2),p.size,p.size);ctx.restore();
      if(im&&p.role===0&&cam.zoom>1.00001){
        const span=540/cam.zoom,sx=540*cam.center[0]-span/2,sy=540*cam.center[1]-span/2,k=p.size/span;
        const ratio=Math.min(498/im.height,492/im.width,e.image.displayLimitPx/(1.5*Math.max(im.width,im.height))),w=im.width*ratio,h=im.height*ratio;
        ctx.save();ctx.beginPath();ctx.rect(rect[0],rect[1],p.size,p.size);ctx.clip();
        ctx.drawImage(board,sx,sy,span,span,rect[0],rect[1],p.size,p.size);
        // 原照片在原画板的同一矩阵上重新取样，避免放大540缓存冒充高分照片。
        ctx.drawImage(im,rect[0]+((540-w)/2-sx)*k,rect[1]+((540-h)/2-sy)*k,w*k,h*k);ctx.restore();
      }
      return rect;
    }
    function text(value,x,y,size,weight=600,align='left',alpha=1,color=foreground){
      if(!value||alpha<=.005)return null;ctx.save();ctx.globalAlpha=alpha;ctx.font=font(size,weight);ctx.textAlign=align;ctx.fillStyle=color;
      const m=ctx.measureText(value),left=align==='center'?x-m.width/2:align==='right'?x-m.width:x;
      ctx.fillText(value,x,y);ctx.restore();return {text:value,fontSize:size,opacity:alpha,rect:[left,y-(m.actualBoundingBoxAscent??size*.86),left+m.width,y+(m.actualBoundingBoxDescent??size*.2)]};
    }
    function caption(e){
      const labels=[],date=e.date||'',status=e.status||'';ctx.font=font(88,500);const dw=ctx.measureText(date).width;
      ctx.font=font(68,500);const sw=ctx.measureText(status).width;let size=104;ctx.font=font(size);
      while(ctx.measureText(e.name).width+dw+48>1776&&size>96){size-=2;ctx.font=font(size);}
      const nw=ctx.measureText(e.name).width;
      if(nw+dw+48<=1776){
        const x=(1920-nw-dw-48)/2;labels.push(text(e.name,x,978,size),text(date,x+nw+48,978,88,500),text(status,960,1060,68,500,'center',1,muted));
      }else{
        let split=1,best=Infinity;for(let k=1;k<e.name.length;k++){const a=e.name.slice(0,k),b=e.name.slice(k),aw=ctx.measureText(a).width,bw=ctx.measureText(b).width;
          const score=Math.abs(aw-(bw+dw+sw+76))+(e.name[k-1]===' '||e.name[k]===' '?0:180);
          if(aw<=1776&&bw+dw+sw+76<=1776&&score<best){split=k;best=score;}
        }
        const a=e.name.slice(0,split),b=e.name.slice(split),bw=ctx.measureText(b).width,x=(1920-bw-dw-sw-76)/2;
        labels.push(text(a,960,968,size,600,'center'),text(b,x,1056,size),text(date,x+bw+48,1056,88,500),text(status,x+bw+dw+76,1056,68,500,'left',1,muted));
      }
      return labels.filter(Boolean).map(l=>({...l,kind:l.text===date?'date':l.text===status?'status':'model'}));
    }
    function style(e){return {material:e.style.kind,color:e.style.color};}
    function actor(s,panels){
      const old=entries[s.old],next=entries[s.target],cp=s.card?clamp((s.t-s.card.cardStart)/(s.card.cardEnd-s.card.cardStart)):1;
      const changing=s.travel||s.card,phase=s.card?smooth((cp-.62)/.35):s.u;
      const pose=.3*(s.old+(s.target-s.old)*smooth(phase)),b=PreviewHero.draw(measure,{scale:1,t:pose,material:'draft'}).bounds;
      const baseW=b[3]-b[1],baseH=b[2]-b[0],height=e=>Math.min(nativeLong(e)<240?265:286,260+26*clamp(((e.actorScale??.93)-.35)/.58));
      const scale=Math.min((height(old)+(height(next)-height(old))*smooth(phase))/baseH,166/baseW);
      const major=s.row.duration>=2,keyRise=major?36:24;
      let hx=s.intro?1680:s.outro?1435+245*smooth((s.t-timeline.outroStart)/.9):1435;
      if(s.card&&timeline.introEnd>0&&s.card.index===chapters[0]?.index)hx=1680-245*smooth((s.t-s.card.cardStart)/.35);
      const hy=s.intro?430+55*(1-smooth(s.t/.7)):s.outro?430-120*smooth((s.t-timeline.outroStart)/1.1):430-(changing?(s.card?65:keyRise)*Math.sin(Math.PI*phase):0);
      const bounds=[hx-baseW*scale/2-5,hy-baseH*scale/2-5,hx+baseW*scale/2+5,hy+baseH*scale/2+5];
      const draw=e=>{ctx.save();ctx.translate(hx,hy);ctx.rotate(-Math.PI/2);PreviewHero.draw(ctx,{scale,t:pose,...style(e)});ctx.restore();};
      const transfer=smooth((phase-.1)/.8),front=bounds[0]+(bounds[2]-bounds[0])*transfer;
      const current=panels.find(p=>p.role===0);
      if(changing&&current&&phase>.07&&phase<.9){
        const x=current.x+current.size/2+27;ctx.save();ctx.globalAlpha=.6*Math.sin(Math.PI*phase);ctx.fillStyle=next.style.color||'#c8bdad';
        ctx.fillRect(x,hy-110,Math.max(12,bounds[0]+9-x),16);ctx.restore();
      }
      if(changing){
        ctx.save();ctx.beginPath();ctx.rect(front,bounds[1],Math.max(0,bounds[2]-front),bounds[3]-bounds[1]);ctx.clip();draw(old);ctx.restore();
        ctx.save();ctx.beginPath();ctx.rect(bounds[0],bounds[1],Math.max(0,front-bounds[0]),bounds[3]-bounds[1]);ctx.clip();draw(next);ctx.restore();
      }else draw(next);
      return {bounds,transfer};
    }
    return t=>{
      const s=state(t),labels=[],panels=[],phoneRects=[];ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';
      ctx.fillStyle='#151411';ctx.fillRect(0,0,1920,1080);const field=ctx.createRadialGradient(985,420,100,960,440,1140);
      field.addColorStop(0,'#39322b');field.addColorStop(1,'#100f0d');ctx.fillStyle=field;ctx.fillRect(0,0,1920,1080);
      let offset=0,velocity=0,boardScale=1,groupIndex=s.main,mode='read';
      if(s.travel){
        mode='handoff';const elapsed=s.t-s.row.start,D=s.row.duration>=2?52:40;
        if(elapsed>=lead){const q=clamp((elapsed-(s.switched?lead+half:lead))/half);offset=s.switched?D*(1-q)**4:-D*q**4;velocity=-4*D/half*(s.switched?(1-q)**3:q**3);}
      }
      if(s.card){
        mode='chapter';const cp=clamp((s.t-s.card.cardStart)/(s.card.cardEnd-s.card.cardStart)),a=1-smooth((cp-.5)/.18);
        const shift=-90*smooth((cp-.5)/.18),title=s.card.title.split('：').pop();
        labels.push(text(`第${s.card.number}章`,960,310+shift,72,500,'center',a,muted),text(s.card.era,960,485+shift,146,600,'center',a),text(title,960,645+shift,104,600,'center',a));
        const arrive=smooth((cp-.72)/.28);groupIndex=s.target;boardScale=.84+.16*arrive;offset=58*(1-arrive);
        if(cp<.72)boardScale=0;
      }
      if(!s.intro&&!s.outro&&boardScale>0){
        [-1,0,1].forEach(role=>{const i=groupIndex+role;if(i<0||i>=entries.length)return;
          const base=role===0?mainSize(entries[i]):280,size=base*boardScale;
          panels.push({i,role,x:role===0?965+(base-size)/2:role<0?225:1695,y:430+(role===0?offset:s.card?offset:0),size});
        });
        const cam=camera(s,entries[s.main]);panels.forEach(p=>phoneRects.push({id:entries[p.i].id,role:p.role,rect:panel(p,cam)}));
        if(!s.card){
          labels.push(...caption(entries[s.main]));
          for(const p of panels)if(p.role){let words=entries[p.i].name,parts=[''];ctx.font=font(48,500);
            for(const char of Array.from(words)){const k=parts.length-1;if(ctx.measureText(parts[k]+char).width>390&&parts[k])parts.push(char);else parts[k]+=char;}
            parts.forEach((part,k)=>labels.push(text(part,p.x,p.y+p.size/2+55+k*56,48,500,'center',1,muted)));
          }
        }
      }
      if(s.intro){
        mode='intro';const dy=35*(1-smooth(s.t/.55));labels.push(text(config.title||'穿过华为手机的22年',96,230+dy,104),text('华为 × 分家前荣耀',96,340+dy,76,500));
        introIds.forEach((i,k)=>{const rise=76*(1-smooth((s.t-k*.1)/.65));panels.push({i,role:k-1,x:[560,965,1370][k],y:640+rise,size:k===1?380:260});});
        panels.forEach(p=>phoneRects.push({id:entries[p.i].id,role:p.role,rect:panel(p,{zoom:1})}));
        labels.push(text(introIds.map(i=>entries[i].year).join('  →  '),960,1002,64,500,'center',1,muted));
      }else if(s.outro){
        mode='ending';const age=s.t-timeline.outroStart,pull=smooth(age/.9),base=mainSize(entries[s.main]);
        const p={i:s.main,role:0,x:965+75*pull,y:430+180*pull,size:base+(420-base)*pull};panels.push(p);phoneRects.push({id:entries[p.i].id,role:0,rect:panel(p,{zoom:1})});
        labels.push(text('设计在变，探索向前',96,210,104,600,'left',smooth((age-.55)/.25)),text('从功能机',96,405,72,500),text('到折叠时代',96,505,72,500),
          text('几代人的接力，才有今天。',96,982,72,500),text('爆裂队长 NEXT · BLCaptain',1848,1058,44,500,'right',1,muted));
      }
      if(!s.intro&&!s.outro&&!s.card){labels.push(text(`第${s.chapter?.number||1}章 · ${s.chapter?.title?.split('：').pop()||''}`,72,52,40,500,'left',1,muted),text(`${s.main+1} / ${entries.length}`,1848,52,40,500,'right',1,muted));}
      const hero=actor(s,panels),touch=(a,b)=>a[0]<b[2]+24&&a[2]>b[0]-24&&a[1]<b[3]+24&&a[3]>b[1]-24;
      const collisions=phoneRects.filter(p=>touch(hero.bounds,p.rect)).length,valid=labels.filter(Boolean),cam=camera(s,entries[s.main]);
      const frameMain=s.intro?introIds[1]:s.main;
      Object.assign(canvas.dataset,{renderTime:s.t.toFixed(4),mainId:entries[frameMain].id,currentId:entries[frameMain].id,chapterIndex:String(s.chapter?.index??0),mode,
        visibleIds:phoneRects.map(p=>p.id).join(','),phoneRects:JSON.stringify(phoneRects),actorBounds:JSON.stringify(hero.bounds),labelRects:JSON.stringify(valid),
        protectionIntersections:String(collisions),fontSizes:JSON.stringify(valid.map(l=>l.fontSize)),nameFont:String(valid.find(l=>l.kind==='model')?.fontSize||96),
        motionAxis:'y',motionDirection:'up',seamOffsetY:String(offset),seamVelocityY:String(velocity),materialTransfer:String(hero.transfer),focusZoom:String(cam.zoom),focusAmount:String(cam.amount),
        outOfFrameLabels:String(valid.filter(l=>l.rect[0]<0||l.rect[1]<0||l.rect[2]>1920||l.rect[3]>1080).length),stable:String(mode==='read'&&cam.amount===0)});
    };
  }
  window.FocusJourney={prepare};
})();
