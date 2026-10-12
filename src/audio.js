/** Original Web Audio synthesis: all sounds are generated locally. */
export class AudioController {
  constructor() {
    this.context = this.ctx = null;
    this.master = null;
    this.volume = .45;
    this.muted = false;
    this.unlocked = false;
    this.voices = 0;
    this.maxVoices = 28;
    this.lastSound = new Map();
    this.ambientTime = 0;
    this.chimeTime = 16;
    this.unlockGesture = () => {void this.unlock();};
    if (typeof document !== "undefined") {
      document.addEventListener("pointerdown",this.unlockGesture);
      document.addEventListener("keydown",this.unlockGesture);
    }
  }

  async unlock() {
    const AudioContext = globalThis.AudioContext || globalThis.webkitAudioContext;
    if(!AudioContext)return false;
    try {
      if(!this.context) {
        this.context = this.ctx = new AudioContext();
        this.master = this.context.createGain();
        this.master.gain.value = this.muted ? 0 : this.volume;
        const compressor=this.context.createDynamicsCompressor();
        compressor.threshold.value=-15;
        compressor.knee.value=12;
        compressor.ratio.value=3;
        compressor.attack.value=.004;
        compressor.release.value=.16;
        this.master.connect(compressor);compressor.connect(this.context.destination);
        this.compressor=compressor;
        this.noiseBuffer=this.context.createBuffer(1,this.context.sampleRate*2,this.context.sampleRate);
        const data=this.noiseBuffer.getChannelData(0);
        let brown=0;
        for(let i=0;i<data.length;i++) {brown=(brown+(Math.random()*2-1)*.02)/1.02;data[i]=brown*3.5+(Math.random()*2-1)*.21;}
      }
      if(this.context.state === "suspended")await this.context.resume();
      this.unlocked = this.context.state === "running";
      if(this.unlocked) {
        document.removeEventListener("pointerdown",this.unlockGesture);
        document.removeEventListener("keydown",this.unlockGesture);
        this.startAmbience();
      }
      return this.unlocked;
    } catch {return false;}
  }

  setMuted(muted) {
    this.muted=Boolean(muted);
    if(this.master)this.master.gain.setTargetAtTime(this.muted?0:this.volume,this.context.currentTime,.035);
    return this.muted;
  }
  toggleMute() {return this.setMuted(!this.muted);}
  setVolume(volume) {
    this.volume=Math.min(1,Math.max(0,Number(volume)||0));
    if(this.master&&!this.muted)this.master.gain.setTargetAtTime(this.volume,this.context.currentTime,.035);
    return this.volume;
  }

  startAmbience() {
    if(this.wind)return;
    const source=this.context.createBufferSource();
    source.buffer=this.noiseBuffer;source.loop=true;
    const filter=this.context.createBiquadFilter();filter.type="lowpass";filter.frequency.value=520;filter.Q.value=.35;
    const gain=this.context.createGain();gain.gain.value=.055;
    source.connect(filter);filter.connect(gain);gain.connect(this.master);source.start();
    this.wind={source,filter,gain};
  }

  envelope(gain,start,duration,volume,attack=.005) {
    gain.gain.setValueAtTime(.0001,start);
    gain.gain.exponentialRampToValueAtTime(Math.max(.0002,volume),start+Math.min(duration*.35,attack));
    gain.gain.exponentialRampToValueAtTime(.0001,start+duration);
  }
  connectVoice(source,filter,duration,volume,{delay=0,pan=0,attack=.005}={}) {
    if(this.voices>=this.maxVoices)return;
    const start=this.context.currentTime+delay;
    const gain=this.context.createGain();
    this.envelope(gain,start,duration,volume,attack);
    const panner=this.context.createStereoPanner?.();
    if(filter){source.connect(filter);filter.connect(gain);}else source.connect(gain);
    if(panner){panner.pan.value=Math.max(-1,Math.min(1,pan));gain.connect(panner);panner.connect(this.master);}else gain.connect(this.master);
    this.voices++;
    source.onended=()=>{source.disconnect();filter?.disconnect();gain.disconnect();panner?.disconnect();this.voices=Math.max(0,this.voices-1);};
    source.start(start);source.stop(start+duration+.01);
  }
  noise(duration,volume,frequency=1800,{endFrequency=frequency,type="bandpass",q=.6,delay=0,pan=0,attack=.005}={}) {
    if(this.voices>=this.maxVoices)return;
    const source=this.context.createBufferSource();source.buffer=this.noiseBuffer;source.loop=true;
    const filter=this.context.createBiquadFilter();filter.type=type;filter.Q.value=q;
    const start=this.context.currentTime+delay;
    filter.frequency.setValueAtTime(Math.max(30,frequency),start);
    filter.frequency.exponentialRampToValueAtTime(Math.max(30,endFrequency),start+duration);
    this.connectVoice(source,filter,duration,volume,{delay,pan,attack});
  }
  tone(frequency,endFrequency,duration,volume,{type="sine",delay=0,pan=0,attack=.004,filterFrequency=2200}={}) {
    if(this.voices>=this.maxVoices)return;
    const source=this.context.createOscillator();source.type=type;
    const start=this.context.currentTime+delay;
    source.frequency.setValueAtTime(Math.max(20,frequency),start);
    source.frequency.exponentialRampToValueAtTime(Math.max(20,endFrequency),start+duration);
    const filter=this.context.createBiquadFilter();filter.type="lowpass";filter.frequency.value=filterFrequency;
    this.connectVoice(source,filter,duration,volume,{delay,pan,attack});
  }

  play(name,{combo=1,heavy=false,speed=0,pan=0}={}) {
    if(!this.unlocked||this.muted||this.context?.state!=="running")return false;
    const now=this.context.currentTime;
    const interval={footstep:.07,hit:.035,heavyHit:.06,enemyDeath:.09,enemyWindup:.1}[name]??.025;
    if(now-(this.lastSound.get(name)??-100)<interval)return false;
    this.lastSound.set(name,now);
    const location={pan};
    if(name==="swing") {
      const duration=[0,.15,.24,.30][combo]??.15;
      this.noise(duration,combo===3?.28:.17,combo===2?850:1450,{...location,endFrequency:combo===3?320:2400,q:.45,attack:.045});
      if(combo===3)this.tone(105,58,.16,.07,location);
      else this.noise(.035,.055,400,{...location,type:"lowpass"});
    } else if(name==="hit"||name==="heavyHit") {
      const strong=heavy||name==="heavyHit";
      this.tone(strong?165:200,strong?58:86,strong?.17:.10,strong?.27:.18,location);
      this.noise(strong?.15:.08,strong?.36:.24,1600,{...location,endFrequency:450});
      this.tone(strong?580:940,strong?390:750,strong?.16:.10,.055,{...location,type:"triangle"});
    } else if(name==="footstep") {
      this.noise(.045,.12+(speed>6?.035:0),1000+Math.random()*500,{...location,type:"lowpass",endFrequency:350});
      this.tone(105+Math.random()*20,65,.035,.045,location);
    } else if(name==="jump") {
      this.noise(.12,.16,900,{...location,endFrequency:2300,attack:.012});
      this.tone(140,105,.09,.045,location);
    } else if(name==="land") {
      this.noise(.07,.17,1100,{...location,type:"lowpass",endFrequency:360});
      this.tone(130,65,.065,.1,location);
    } else if(name==="dodge") {
      this.noise(.18,.17,1800,{...location,endFrequency:650,attack:.025});
    } else if(name==="enemyWindup") {
      this.noise(.21,.1,360,{...location,endFrequency:720,q:1,attack:.03});
      this.tone(135,95,.18,.025,{...location,type:"triangle",filterFrequency:500});
    } else if(name==="enemyAttack") {
      this.noise(.22,.18,650,{...location,endFrequency:1700,attack:.01});
    } else if(name==="playerHit") {
      this.tone(120,46,.2,.21,location);
      this.noise(.14,.24,1500,{...location,endFrequency:260});
    } else if(name==="enemyDeath") {
      this.noise(.65,.19,1200,{...location,endFrequency:210,type:"highpass",attack:.055});
      this.tone(440,445,.6,.035,{...location,type:"triangle",delay:.14});
      this.tone(660,656,.65,.025,{...location,delay:.25});
    } else if(name==="interact"||name==="collect") {
      this.tone(660,659,.2,.07,{...location,type:"triangle"});
      this.tone(880,875,.27,.045,{...location,delay:.065});
    } else if(name==="heal") {
      for(let i=0;i<3;i++)this.tone([330,440,660][i],[330,440,660][i],.6,.045,{...location,delay:i*.14});
    } else if(name==="victory") {
      for(let i=0;i<4;i++)this.tone([330,440,550,660][i],[330,440,550,660][i],.9,.065,{...location,type:"triangle",delay:i*.19,attack:.02});
    } else return false;
    return true;
  }

  update(dt,{combat=false}={}) {
    if(!this.unlocked)return;
    this.ambientTime+=dt;
    if(this.wind) {
      const now=this.context.currentTime;
      this.wind.filter.frequency.setTargetAtTime(470+Math.sin(this.ambientTime*.19)*130,now,.4);
      this.wind.gain.gain.setTargetAtTime((combat?.035:.055)*( .8+Math.sin(this.ambientTime*.31)*.2 ),now,.5);
    }
    this.chimeTime-=dt;
    if(this.chimeTime<=0) {
      this.chimeTime=18+Math.random()*18;
      if(!combat&&!this.muted) {
        const frequency=[440,550,660][Math.floor(Math.random()*3)];
        this.tone(frequency,frequency*.998,2.4,.022,{type:"sine",pan:Math.random()*.8-.4,attack:.02});
        this.tone(frequency*2.01,frequency*2,1.25,.011,{type:"triangle",pan:-.25,attack:.01});
      }
    }
  }
  dispose() {
    document.removeEventListener("pointerdown",this.unlockGesture);
    document.removeEventListener("keydown",this.unlockGesture);
    this.wind?.source.stop();this.wind?.source.disconnect();
    if(this.context&&this.context.state!=="closed")void this.context.close();
  }
}
