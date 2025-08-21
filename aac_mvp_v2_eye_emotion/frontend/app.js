
const e = React.createElement;
const { useState, useEffect, useRef } = React;

const API = (path, opts={}) => fetch(`http://127.0.0.1:8000${path}`, opts).then(r=>r.json());

const SYMBOLS = [
  {text:'I'},{text:'want'},{text:'help'},{text:'more'},
  {text:'stop'},{text:'yes'},{text:'no'},{text:'toilet'},
  {text:'drink'},{text:'eat'},{text:'play'},{text:'thanks'}
];

const MODES = ['touch','switches','eye'];

function usePrediction(phrase, setSuggestion){
  useEffect(()=>{
    let ignore=false;
    (async ()=>{
      try{
        const res = await API('/api/predict',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({history: phrase})});
        if(!ignore) setSuggestion(res.suggestion||'');
      }catch(e){ if(!ignore) setSuggestion(''); }
    })();
    return ()=>{ ignore=true; };
  },[phrase]);
}

function useWebcam(){
  const videoRef = useRef(null);
  useEffect(()=>{
    (async ()=>{
      try{
        const stream = await navigator.mediaDevices.getUserMedia({video:true, audio:false});
        if(videoRef.current) videoRef.current.srcObject = stream;
      }catch(e){ console.warn('webcam', e); }
    })();
  },[]);
  return videoRef;
}

function mapBlendshapesToEmotion(blendshapes){
  if(!blendshapes || blendshapes.length===0) return {label:'unknown', score:0};
  const scores = Object.fromEntries(blendshapes.map(bs => [bs.categoryName, bs.score]));
  const smile = (scores['mouthSmileLeft']||0 + scores['mouthSmileRight']||0)/2;
  const browDown = (scores['browDownLeft']||0 + scores['browDownRight']||0)/2;
  const eyeBlink = (scores['eyeBlinkLeft']||0 + scores['eyeBlinkRight']||0)/2;
  const mouthFrown = (scores['mouthFrownLeft']||0 + scores['mouthFrownRight']||0)/2;
  if(smile > 0.6) return {label:'happiness', score:smile};
  if(browDown > 0.5 && mouthFrown > 0.4) return {label:'anger', score:(browDown+mouthFrown)/2};
  if(mouthFrown > 0.5 && smile < 0.3) return {label:'sadness', score:mouthFrown};
  if(eyeBlink > 0.6) return {label:'tired', score:eyeBlink};
  return {label:'neutral', score:0.5};
}

function App(){
  const [phrase, setPhrase] = useState('');
  const [suggestion, setSuggestion] = useState('');
  const [blocked, setBlocked] = useState([]);
  const [plan, setPlan] = useState('Basic');
  const [bestMethod, setBestMethod] = useState('touch');
  const [mode, setMode] = useState('touch');

  const [emotion, setEmotion] = useState('unknown');
  const [landmarker, setLandmarker] = useState(null);

  // Init MediaPipe FaceLandmarker
  const videoRef = useWebcam();
  useEffect(()=>{
    (async ()=>{
      const vision = await window.FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.5/wasm"
      );
      const lm = await window.FaceLandmarker.createFromOptions(vision, {
        baseOptions: { modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task" },
        outputFaceBlendshapes: true,
        runningMode: "VIDEO",
        numFaces: 1
      });
      setLandmarker(lm);
    })();
  },[]);

  // Emotion tracking loop
  useEffect(()=>{
    let rafId;
    const loop = ()=>{
      const v = videoRef.current;
      if(landmarker && v && v.readyState >= 2){
        const ts = performance.now();
        const res = landmarker.detectForVideo(v, ts);
        if(res && res.faceBlendshapes && res.faceBlendshapes.length){
          const mapped = mapBlendshapesToEmotion(res.faceBlendshapes[0].categories || []);
          setEmotion(mapped.label);
        }
      }
      rafId = requestAnimationFrame(loop);
    };
    rafId = requestAnimationFrame(loop);
    return ()=> cancelAnimationFrame(rafId);
  },[landmarker, videoRef]);

  // Eye tracking via WebGazer
  const [hoverIndex, setHoverIndex] = useState(-1);
  const dwellRef = useRef({index:-1, start:0});
  useEffect(()=>{
    if(mode !== 'eye') return;
    window.webgazer.setGazeListener((data, timestamp)=>{
      if(!data) return;
      const x = data.x; const y = data.y;
      const grid = document.getElementById('aac-grid');
      if(!grid) return;
      const rect = grid.getBoundingClientRect();
      if(x < rect.left || x > rect.right || y < rect.top || y > rect.bottom){
        setHoverIndex(-1); return;
      }
      const cols = 4, rows = Math.ceil(SYMBOLS.length/4);
      const col = Math.min(cols-1, Math.max(0, Math.floor((x-rect.left)/(rect.width/cols))));
      const row = Math.min(rows-1, Math.max(0, Math.floor((y-rect.top)/(rect.height/rows))));
      const idx = row*cols + col;
      setHoverIndex(idx);
      // dwell selection
      const now = performance.now();
      if(dwellRef.current.index !== idx){
        dwellRef.current = {index: idx, start: now};
      }else{
        const dwellMs = 1200; // 1.2s
        if(now - dwellRef.current.start > dwellMs){
          const card = document.querySelector(`[data-idx="${idx}"]`);
          if(card){ card.click(); dwellRef.current.start = now + 999999; } // prevent re-fire
        }
      }
    }).begin();
    // optional: set regression model & parameters
    window.webgazer.showVideoPreview(false).showPredictionPoints(false);
    return ()=>{ try{ window.webgazer.end(); }catch(e){} };
  },[mode]);

  // Fetch blocked words at start
  useEffect(()=>{
    (async ()=>{
      try{
        const bl = await API('/api/parent/blocklist');
        setBlocked(bl.blocked||[]);
      }catch(e){}
    })();
  },[]);

  usePrediction(phrase, setSuggestion);

  function adaptUIByEmotion(){
    return (emotion==='sadness'||emotion==='anger'||emotion==='tired') ? 'Simpler layout & slower rate' : 'Normal';
  }

  async function addWord(w){
    const newPhrase = (phrase + ' ' + w).trim();
    setPhrase(newPhrase);
    // input metrics
    API('/api/input/metrics',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({method: mode==='eye'?'eye':(mode==='switches'?'switches':'touch'), selections:1, errors:0, avg_time_ms: mode==='eye'?900:700})
    }).then(r=> setBestMethod(r.best_method));
    // TTS
    try{ speechSynthesis.speak(new SpeechSynthesisUtterance(w)); }catch(e){}
  }

  async function blockWord(word){
    await API('/api/parent/blocklist',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({word})});
    const bl = await API('/api/parent/blocklist'); setBlocked(bl.blocked||[]);
  }

  async function claimReferral(email, joined){
    await API('/api/referrals/claim',{method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({referrer_email:email, joined_email: joined})});
    const res = await API('/api/referrals/plan?email='+encodeURIComponent(email)); setPlan(res.plan||'Basic');
  }

  const filteredSymbols = SYMBOLS.filter(s => !blocked.includes((s.text||'').toLowerCase()));
  return e ('div', null,
    e('div', {className:'header'},
      e('h1', {style:{fontSize:18, margin:0}}, 'Smart Adaptive AAC — v2'),
      e('span', {className:'badge'}, 'Best input: '+bestMethod),
      e('span', {className:'badge'}, 'Emotion: '+emotion),
      e('span', {className:'badge'}, 'Adaptive: '+adaptUIByEmotion()),
      e('span', {className:'badge'}, 'Plan: '+plan),
    ),
    e('div', {className:'main'},
      e('div', {className:'board'},
        e('div', {className:'mode-switch'},
          MODES.map(m=> e('button', {key:m, onClick:()=>setMode(m), className: 'mode-switch-btn '+(mode===m?'active':'' )}, m.toUpperCase()))
        ),
        e('h3', null, 'AAC Board ('+mode+')'),
        e('div', {id:'aac-grid', className:'grid'},
          filteredSymbols.map((s,i)=> e('div', {
              key:i, 'data-idx':i, className: 'card '+(i===hoverIndex && mode==='eye' ? 'highlight':''),
              onClick:()=> addWord(s.text)
            }, s.text))
        ),
        e('div', {style:{marginTop:10}},
          e('textarea', {value: phrase, onChange:(ev)=>setPhrase(ev.target.value)}),
          e('div', {className:'small'}, 'Suggestion: ', suggestion)
        )
      ),
      e('div', {className:'panel'},
        e('h3', null, 'Parent Dashboard'),
        e('div', {className:'controls'},
          e('input', {placeholder:'Block word...', id:'block'}),
          e('button', {className:'button', onClick:()=>{
            const v = document.getElementById('block').value.trim().toLowerCase(); if(v) blockWord(v);
          }}, 'Block')
        ),
        e('div', {className:'small', style:{marginTop:8}}, 'Blocked: ', blocked.join(', ')||'None'),
        e('hr'),
        e('div', {className:'controls'},
          e('input', {placeholder:'Your email', id:'refe'}),
          e('input', {placeholder:"Friend's email", id:'join'}),
          e('button', {className:'button', onClick:()=>{
            const a = document.getElementById('refe').value.trim();
            const b = document.getElementById('join').value.trim();
            if(a && b) claimReferral(a,b);
          }}, 'Claim referral')
        ),
        e('hr'),
        e('h4', null, 'Camera'),
        e('video', {ref: videoRef, autoPlay:true, muted:true, playsInline:true})
      )
    )
  )
}

ReactDOM.createRoot(document.getElementById('app')).render(e(App));
