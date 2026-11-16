import React from 'react';
import {AbsoluteFill, Audio, Composition, Easing, Freeze, Img, OffthreadVideo, Sequence, cancelRender, continueRender, delayRender, interpolate, registerRoot, staticFile, useCurrentFrame} from 'remotion';
import D from '../episode.compiled.json';
const THEMES = {
  'paper-red': {paper:'#fff6e9', accent:'#cb2439', ink:'#292432', depth:'#791c2a', radius:3},
  'speed-yellow': {paper:'#fff9d6', accent:'#ffe23f', ink:'#252932', depth:'#8f711b', radius:22},
  'berry-progress': {paper:'#fff1ed', accent:'#b82060', ink:'#2c213c', depth:'#741540', radius:8},
};
const T=THEMES[D.style], L=D.visualLayout;
const clamp={extrapolateLeft:'clamp', extrapolateRight:'clamp'} as const;
const hold=delayRender('Load exact audited font files; system fallback is disabled');
Promise.all(Object.entries(D.fonts).map(async ([role,file])=>{
  const name=role==='title'?'Title':role==='subtitle'?'Subtitle':'Body';
  const face=new FontFace(name,`url(${staticFile(file as string)})`,{weight:String(D.fontAudit[role].selectedWeight)});
  document.fonts.add(await face.load());
})).then(()=>document.fonts.ready).then(()=>continueRender(hold)).catch(cancelRender);
const fontStyle=(role='body')=>({fontFamily:role==='title'?'Title':role==='subtitle'?'Subtitle':'Body',fontWeight:D.fontAudit[role].selectedWeight,fontSynthesis:'none'} as React.CSSProperties);
const B=({children,style={}}:any)=><div style={{...fontStyle(),...style}}>{children}</div>;

function Background(){
  const f=useCurrentFrame();
  return <AbsoluteFill style={{background:T.paper,overflow:'hidden'}}>
    {D.background?.asset&&<Img src={staticFile(D.background.asset)} style={{position:'absolute',left:-90,top:-90,width:1260,height:2100,objectFit:'cover',filter:'blur(20px) brightness(1.8)',opacity:.16,transform:`translate(${Math.sin(f/190)*8}px,${Math.cos(f/170)*8}px)`}}/>}
    <AbsoluteFill style={{background:`radial-gradient(ellipse at 0% 100%,${T.accent}1c,transparent 60%),radial-gradient(ellipse at 100% 0%,#ffffffb0,transparent 50%)`}}/>
    <svg width={1080} height={1920} style={{position:'absolute'}}><defs>
      <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".045 .19" numOctaves={3} seed={23}/><feColorMatrix type="saturate" values="0"/></filter>
      <pattern id="dots" width={28} height={28} patternUnits="userSpaceOnUse"><circle cx={4} cy={4} r={1.3} fill={T.ink} opacity={.14}/></pattern>
    </defs><rect width={1080} height={1920} filter="url(#grain)" opacity={.16} style={{mixBlendMode:'multiply'}}/><rect x={860} y={40} width={220} height={150} fill="url(#dots)"/><rect y={1730} width={240} height={190} fill="url(#dots)"/></svg>
  </AbsoluteFill>;
}
function Header(){
  const speed=D.style==='speed-yellow';
  return <div data-visual="header" style={{position:'absolute',top:L.headerTop,left:60,right:60,textAlign:'center',...fontStyle('title'),lineHeight:1.18}}>
    {D.mainTitle.map((line,i)=>{
      const emphasis=i===D.mainTitle.length-1;
      return <div key={i} style={{fontSize:L.mainSizes[i],marginTop:i?12:0,padding:emphasis?'12px 8px 18px':0,background:emphasis?(speed?T.ink:T.accent):'transparent',color:emphasis?(speed?T.accent:'#fff9ed'):T.ink,boxShadow:emphasis?`0 9px 0 ${T.depth}`:'none',textShadow:emphasis?`0 2px 0 ${T.depth},0 4px 0 ${T.depth}`:'0 2px 0 #ffffff'}}>{line}</div>;
    })}
    <div style={{...fontStyle('subtitle'),fontSize:L.subtitleSize,lineHeight:1.4,marginTop:18,padding:'8px 10px',background:speed?'#ffffffaa':'#fffdf5b0',color:T.ink}}>{D.subtitle.map((line,i)=><div key={i}>{line}</div>)}</div>
  </div>;
}
function Media({s,cover=false}:any){
  const f=useCurrentFrame();const [left,top,width,height]=cover?L.coverPicture:L.picture;
  const scale=1+(s.kind==='image'&&!cover&&!s.mark&&!s.marks?interpolate(f,[0,Math.max(1,s.frames-1)],[0,.018],clamp):0);
  let style:any={width:'100%',height:'100%',objectFit:'cover',objectPosition:s.focus??'50% 50%',transform:`scale(${scale})`};
  if(s.crop){const [x,y,w,h]=s.crop;const sc=Math.max(width/w,height/h);style={position:'absolute',width:s.sourceWidth*sc,height:s.sourceHeight*sc,left:(width-w*sc)/2-x*sc,top:(height-h*sc)/2-y*sc};}
  const marks=s.marks??(s.mark?[{rect:s.mark,from:s.markFrom??6}]:[]);
  return <div data-visual="picture" style={{position:'absolute',left,top,width,height,overflow:'hidden',borderRadius:T.radius,boxShadow:'0 12px 28px #372b2520'}}>
    {s.kind==='video'?<OffthreadVideo src={staticFile(s.asset)} muted playbackRate={s.rate??1} style={style}/>:<Img src={staticFile(s.asset)} style={style}/>}
    {marks.map((m,i)=><div key={i} style={{position:'absolute',left:m.rect[0]*width,top:m.rect[1]*height,width:m.rect[2]*width,height:m.rect[3]*height,background:'#ffe22c',opacity:.30*interpolate(f,[m.from??6,(m.from??6)+6],[0,1],clamp),mixBlendMode:'multiply'}}/>)}
  </div>;
}
function Text({text,lines,keywords=[],progressive=false,frames=120,paint=false}:any){
  const f=useCurrentFrame();const rows=lines??text.split('\n');const flat=rows.join('');const length=[...flat].length;
  const reveal=Math.max(1,Math.min(frames-30,length*1.8));const seen=progressive?Math.floor(interpolate(f,[0,reveal],[0,length],clamp)):length;
  const points=[...flat];const marked=new Set<number>();
  for(const word of keywords){const needle=[...word];if(!needle.length)continue;for(let a=0;a<=points.length-needle.length;a++){if(points.slice(a,a+needle.length).join('')===word)for(let b=a;b<a+needle.length;b++)marked.add(b);}}
  let cursor=0;
  return <>{rows.map((line,j)=><div key={j}>{[...line].map((ch,i)=>{const k=cursor++,hi=marked.has(k);return <span key={i} style={{opacity:k<seen?1:0,color:hi?(paint?'#ffe34e':T.ink):undefined,background:hi&&!paint?'#ffe779':undefined,boxShadow:hi&&!paint?'0 3px 0 #ffe779':undefined}}>{ch}</span>;})}</div>)}</>;
}
function Info({info}:any){
  if(!info)return null;
  const card={background:'#fffdf5',borderRadius:T.radius,padding:'20px 22px',boxShadow:`0 8px 0 ${T.accent}24`};
  if(info.type==='metrics'||info.type==='comparison')return <div style={{display:'flex',gap:12}}>{info.items.map((it,i)=><div key={i} style={{...card,flex:1,background:it.active?(D.style==='speed-yellow'?T.ink:T.accent):'#fffdf5',color:it.active?(D.style==='speed-yellow'?T.accent:'#fff9ed'):T.ink}}><B style={{fontSize:36}}>{it.label}</B><div style={{...fontStyle('title'),fontSize:it.valueSize??(info.type==='comparison'?96:85),lineHeight:1.2,marginTop:8}}>{it.value}</div></div>)}</div>;
  if(info.type==='progression')return <div style={card}><div style={{display:'flex',gap:12,justifyContent:'center'}}>{info.steps.map((s,i)=><B key={i} style={{background:i===info.active?T.accent:'#ede2e7',color:i===info.active&&D.style!=='speed-yellow'?'#fff9ed':T.ink,fontSize:37,padding:'8px 18px'}}>{s}</B>)}</div><B style={{fontSize:53,marginTop:17,color:D.style==='speed-yellow'?T.ink:T.accent}}>{info.headline}</B>{info.condition&&<B style={{fontSize:37,marginTop:9,color:T.ink}}>{info.condition}</B>}</div>;
  return <div style={{...card,borderTop:`7px solid ${T.accent}`,color:T.ink}}>{info.heading&&<B style={{fontSize:38,marginBottom:9}}>{info.heading}</B>}{(info.renderLines??info.lines??[]).map((line,i)=><B key={i} style={{fontSize:48,lineHeight:1.4}}><Text text={line} keywords={info.keywords??[]}/></B>)}</div>;
}
function Scene({s,enter=false}:any){
  const f=useCurrentFrame();const fade=enter?interpolate(f,[0,L.transitionFrames],[0,1],{...clamp,easing:Easing.bezier(.22,.61,.36,1)}):1;
  return <AbsoluteFill style={{opacity:fade}}><Media s={s}/>{D.mode==='news'?<div data-visual="board" style={{position:'absolute',left:48,right:48,top:L.boardTop,textAlign:'center',background:D.style==='speed-yellow'?T.ink:D.style==='berry-progress'?'#fffaf7':'#fffdf5',borderTop:D.style==='paper-red'?`8px solid ${T.accent}`:undefined,borderBottom:D.style==='speed-yellow'?`9px solid ${T.accent}`:undefined,borderLeft:D.style==='berry-progress'?`7px solid ${T.accent}`:undefined,borderRadius:T.radius,padding:'23px 20px 30px',boxShadow:D.style==='speed-yellow'?'0 8px 0 #bfa744':'0 9px 26px #372b2514'}}><B style={{fontSize:L.bodySize,lineHeight:1.5,color:D.style==='speed-yellow'?'#fffdf0':T.ink}}><Text text={s.caption??''} lines={s.captionLines} keywords={s.keywords??[]} progressive frames={s.frames}/></B></div>:<div data-visual="board" style={{position:'absolute',left:48,right:48,top:L.boardTop,textAlign:'center'}}><Info info={s.info}/></div>}</AbsoluteFill>;
}
function Cover(){
  const words=D.cover.keywords??[];
  return <AbsoluteFill><Background/><Header/><Media cover s={{asset:D.cover.asset,kind:'image',focus:D.cover.focus,frames:1}}/>{words.length>0&&<div data-visual="cover-keywords" style={{position:'absolute',left:100,right:100,top:L.coverKeywordsTop,textAlign:'center',background:D.style==='speed-yellow'?T.ink:T.accent,color:D.style==='speed-yellow'?T.accent:'#fff9ed',padding:'22px 12px',boxShadow:`0 8px 0 ${T.depth}`,...fontStyle('title'),fontSize:61,lineHeight:1.35}}>{words.map((t,i)=><div key={i}>{t}</div>)}</div>}</AbsoluteFill>;
}
function Film(){
  return <AbsoluteFill><Background/><Header/><Audio src={staticFile('mix.wav')}/>{D.segments.map((s,i)=><React.Fragment key={i}>
    {i>0&&<Sequence from={s.startFrame} durationInFrames={L.transitionFrames} premountFor={30}><Freeze frame={D.segments[i-1].frames-1}><Scene s={D.segments[i-1]}/></Freeze></Sequence>}
    <Sequence from={s.startFrame} durationInFrames={s.frames} premountFor={30}><Scene s={s} enter={i>0}/></Sequence>
  </React.Fragment>)}{D.mode==='speech'&&D.subtitles.map((s,i)=><Sequence key={i} from={s.a} durationInFrames={s.b-s.a} premountFor={30}><B style={{position:'absolute',left:60,right:60,top:L.picture[1]+L.picture[3]-160,fontSize:54,lineHeight:1.35,textAlign:'center',color:'white',WebkitTextStroke:'2px #13161c',paintOrder:'stroke fill',textShadow:'0 3px 7px #000d'}}><Text text={s.text} lines={s.lines} keywords={s.keywords} paint/></B></Sequence>)}<Sequence durationInFrames={3}><Freeze frame={0}><Cover/></Freeze></Sequence></AbsoluteFill>;
}
registerRoot(()=><><Composition id="News" component={Film} durationInFrames={D.frames} width={1080} height={1920} fps={30}/><Composition id="Cover" component={Cover} durationInFrames={1} width={1080} height={1920} fps={30}/></>);
