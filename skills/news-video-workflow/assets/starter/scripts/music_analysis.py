"""Candidate onsets from the exact music excerpt; listening remains necessary."""
import numpy as np

def analyze(samples,sr,segments):
 mono=np.mean(samples,axis=1);window=2048;hop=480
 if len(mono)<window:return {'candidateOnsets':[],'warning':'Excerpt too short for analysis'}
 frames=np.lib.stride_tricks.sliding_window_view(mono,window)[::hop]
 spectrum=np.abs(np.fft.rfft(frames*np.hanning(window),axis=1))
 novelty=np.maximum(0,np.diff(spectrum,axis=0,prepend=spectrum[:1])).sum(axis=1)
 novelty=np.convolve(novelty,[.25,.5,.25],mode='same');threshold=np.median(novelty)+.5*np.std(novelty);peaks=[]
 for i in range(1,len(novelty)-1):
  if novelty[i]>threshold and novelty[i]>=novelty[i-1] and novelty[i]>novelty[i+1]:
   if peaks and (i-peaks[-1])*hop/sr<.15:
    if novelty[i]>novelty[peaks[-1]]:peaks[-1]=i
   else:peaks.append(i)
 onsets=[{'seconds':round((i*hop+window/2)/sr,3),'frame':round((i*hop+window/2)/sr*30),'salience':round(float(novelty[i]/(novelty.max()+1e-12)),3)} for i in peaks]
 cuts=[]
 for s in segments[1:]:
  at=s['startFrame']/30;nearest=min(onsets,key=lambda x:abs(x['seconds']-at)) if onsets else None
  cuts.append({'cutSeconds':round(at,3),'nearestCandidate':nearest,'distanceFrames':round(abs(nearest['seconds']-at)*30) if nearest else None})
 return {'method':'Spectral-flux candidate onsets on the actual selected continuous excerpt','candidateOnsets':onsets,'cutAlignmentCandidates':cuts,'doesNotJudgeMusicStyleOrPopularity':True,'manualListeningRequired':True,'note':'Do not shift speech/lip sync or remove reading hold just to hit a candidate.'}
