"""空配色的真实回归：Canvas梯度必须始终收到有效颜色。"""
import subprocess
import unittest
from pathlib import Path


class HeroTests(unittest.TestCase):
    def test_null_color_does_not_break_any_material(self):
        root = Path(__file__).resolve().parents[1]
        js = r'''
const fs=require('fs'),vm=require('vm');
const pathMethods={moveTo(){},lineTo(){},closePath(){},arc(){},ellipse(){}};
let stops=0;
const gradient={addColorStop(position,color){if(typeof color!=='string'||!color.startsWith('#'))throw Error('无效梯度颜色');stops++;}};
const ctx=new Proxy({createLinearGradient(){return gradient;}},{get(target,key){return target[key]||(()=>{});},set(target,key,value){target[key]=value;return true;}});
const sandbox={window:{},Path2D:function(){Object.assign(this,pathMethods);}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),sandbox);
for(const material of ['draft','glass','metal','pearl','leather','ceramic','carbon','ink','lcd'])sandbox.window.PreviewHero.draw(ctx,{material,color:null,t:1});
if(stops<30)throw Error('没有执行真实梯度分支');
const first=sandbox.window.PreviewHero.draw(ctx,{t:2,scale:1,x:0,y:0}).bounds;
const moved=sandbox.window.PreviewHero.draw(ctx,{t:2,scale:.5,x:100,y:200}).bounds;
if(first.length!==4||first.some(v=>!Number.isFinite(v)))throw Error('边界无效');
for(let i=0;i<4;i++)if(Math.abs(moved[i]-(first[i]*.5+(i%2?200:100)))>2)throw Error('边界缩放或平移错误');
if(first[2]-first[0]<530||first[3]-first[1]<180)throw Error('边界遗漏肢体或披风');
'''
        result = subprocess.run(['node', '-e', js, str(root / 'skills/huawei-phone-journey/src/hero.js')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
