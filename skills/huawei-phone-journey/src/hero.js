/* 独立的程序化飞行角色：同一关节与披风，按画板裁切使用不同绘画材质。 */
(() => {
  const polygon = points => {
    const p = new Path2D();
    p.moveTo(...points[0]);
    points.slice(1).forEach(x => p.lineTo(...x));
    p.closePath();
    return p;
  };
  function limb(a, b, width) {
    const angle = Math.atan2(b[1]-a[1], b[0]-a[0]);
    const p = new Path2D();
    p.arc(...a, width, angle+Math.PI/2, angle+Math.PI*1.5);
    p.arc(...b, width*.72, angle-Math.PI/2, angle+Math.PI/2);
    p.closePath();
    return p;
  }
  function surface(c, p, material, color, seed) {
    c.save(); c.clip(p);
    const grad = c.createLinearGradient(-150,-95,90,90);
    if(material==='draft') {
      c.fillStyle='#f2f0e9'; c.fill(p);
      c.strokeStyle='rgba(45,61,78,.18)'; c.lineWidth=.7;
      for(let y=-180;y<170;y+=9){c.beginPath();c.moveTo(-300,y);c.lineTo(260,y+80);c.stroke();}
    } else if(material==='glass') {
      grad.addColorStop(0,'#d0f6ff');grad.addColorStop(.43,color);grad.addColorStop(.75,'#686fd2');grad.addColorStop(1,'#f1f2ff');
      c.fillStyle=grad;c.fill(p);
      for(let i=0;i<28;i++){
        const x=-300+i*23,y=-105+Math.sin(i*1.9+seed)*65;
        const q=polygon([[x,y],[x+64,y-25],[x+40,y+70]]);
        c.fillStyle=i%3?'rgba(239,254,255,.20)':'rgba(43,64,145,.27)';c.fill(q);
        c.strokeStyle='rgba(225,255,255,.36)';c.lineWidth=.8;c.stroke(q);
      }
    } else if(material==='metal') {
      ['#202832','#d8dedc','#fafdf5','#5f666b','#b6bec0'].forEach((v,i)=>grad.addColorStop(i/4,v));
      c.fillStyle=grad;c.fill(p);c.strokeStyle='rgba(25,29,34,.11)';c.lineWidth=.5;
      for(let y=-180;y<180;y+=3){c.beginPath();c.moveTo(-300,y);c.lineTo(250,y+40);c.stroke();}
    } else if(material==='pearl') {
      grad.addColorStop(0,'#dce4ec');grad.addColorStop(.35,'#fff8ed');grad.addColorStop(.7,'#eae1e9');grad.addColorStop(1,'#fcfff9');
      c.fillStyle=grad;c.fill(p);
      for(let i=0;i<45;i++){
        const x=-280+(i*71%550),y=-135+(i*43%285);
        c.fillStyle=['rgba(196,217,221,.27)','rgba(234,198,216,.24)','rgba(242,232,193,.36)'][i%3];
        c.beginPath();c.ellipse(x,y,23+i%17,8+i%9,-.5,0,Math.PI*2);c.fill();
        c.strokeStyle='rgba(255,255,255,.55)';c.lineWidth=1;c.stroke();
      }
    } else if(material==='leather') {
      grad.addColorStop(0,'#e0a494');grad.addColorStop(.4,color);grad.addColorStop(1,'#541f26');
      c.fillStyle=grad;c.fill(p);c.fillStyle='rgba(38,14,20,.23)';
      for(let x=-300;x<270;x+=5)for(let y=-140;y<150;y+=5){
        c.beginPath();c.ellipse(x+Math.sin(x+y),y,.8,.45,.3,0,Math.PI*2);c.fill();
      }
      c.setLineDash([3,4]);c.strokeStyle='rgba(248,214,182,.57)';c.lineWidth=1;c.stroke(p);c.setLineDash([]);
    } else if(material==='ceramic') {
      grad.addColorStop(0,'#f6f1ed');grad.addColorStop(.5,color);grad.addColorStop(.76,'#fffef5');grad.addColorStop(1,'#7b838a');
      c.fillStyle=grad;c.fill(p);c.strokeStyle='rgba(255,255,255,.85)';c.lineWidth=5;
      c.beginPath();c.moveTo(-230,-16);c.quadraticCurveTo(-45,-96,190,-49);c.stroke();
    } else if(material==='carbon') {
      c.fillStyle='#26313a';c.fill(p);c.lineWidth=3;
      for(let x=-420;x<420;x+=8){
        c.strokeStyle=x%16?'#405565':'#18212b';c.beginPath();c.moveTo(x,-180);c.lineTo(x+290,180);c.stroke();
        c.strokeStyle='rgba(163,184,195,.24)';c.beginPath();c.moveTo(x,180);c.lineTo(x+290,-180);c.stroke();
      }
    } else if(material==='ink') {
      c.fillStyle='#ddd7cc';c.fill(p);c.strokeStyle='rgba(29,39,47,.65)';c.lineWidth=1;
      for(let x=-420;x<420;x+=6){c.beginPath();c.moveTo(x,-180);c.lineTo(x+150,180);c.stroke();}
      c.lineWidth=4;c.stroke(p);
    } else {
      c.fillStyle=color;c.fill(p);c.fillStyle='rgba(22,43,43,.27)';
      for(let x=-300;x<270;x+=5)for(let y=-140;y<150;y+=5)c.fillRect(x,y,2,2);
    }
    c.restore();
    c.strokeStyle=material==='draft'?'#667582':'rgba(37,44,54,.63)';
    c.lineWidth=material==='draft'?1.5:1.1;c.stroke(p);
  }
  function draw(c,{x=0,y=0,scale=1,t=0,material='draft',color='#8db7cc'}={}) {
    color=typeof color==='string'&&/^#[0-9a-f]{6}$/i.test(color)?color:'#77bfcf';
    c.save();c.translate(x,y+Math.sin(t*1.7)*3);c.scale(scale,scale);c.rotate(-.035);
    const wave=Math.sin(t*2.1)*10;
    const cape=polygon([[-20,-46],[-112,-64],[-258,-89+wave],[-222,-39-wave],[-286,0+wave],[-125,-5],[-37,-18]]);
    const parts=[cape,limb([-72,10],[-146,66],16),limb([-146,66],[-226,81],12),
      limb([-67,1],[-163,15],19),limb([-163,15],[-251,38],13),
      limb([55,-31],[116,5],14),limb([116,5],[173,-1],10),
      polygon([[-94,-20],[-57,-39],[20,-50],[68,-37],[73,-5],[22,20],[-42,24],[-88,12]]),
      limb([46,-36],[132,-66],17),limb([132,-66],[215,-70],11),
      polygon([[210,-79],[237,-79],[248,-74],[240,-63],[212,-61]])];
    const head=new Path2D();head.ellipse(80,-61,23,28,-.16,0,Math.PI*2);parts.push(head);
    parts.forEach((p,i)=>surface(c,p,material,color,i));
    c.strokeStyle=material==='draft'?'#536575':'rgba(32,37,44,.66)';c.lineWidth=1.2;
    c.beginPath();c.moveTo(81,-68);c.lineTo(93,-67);c.lineTo(97,-58);c.lineTo(91,-56);c.stroke();
    c.beginPath();c.moveTo(-53,-29);c.quadraticCurveTo(9,-17,52,-27);c.moveTo(-43,12);c.lineTo(21,6);c.stroke();
    if(material==='glass'||material==='metal'){
      c.strokeStyle='rgba(255,255,255,.7)';c.lineWidth=2;
      c.beginPath();c.moveTo(-71,-22);c.lineTo(12,-40);c.lineTo(51,-32);c.stroke();
    }
    c.restore();
  }
  window.PreviewHero={draw};
})();
