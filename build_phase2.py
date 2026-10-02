"""
Build Phase 2 index.html for Dhvaani.
Run: python build_phase2.py
"""
import os

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dhvaani — Your Voice, Your Rights</title>
<meta name="description" content="Dhvaani helps rural citizens speak to government in Tamil, Hindi or English to find welfare schemes and file grievances — no forms, just your voice.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Noto+Sans+Tamil:wght@400;600;700&family=Noto+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --saffron: #FF6B00;
  --saffron-light: #FF8C38;
  --saffron-glow: rgba(255,107,0,0.18);
  --india-blue: #0A2E6E;
  --india-blue-mid: #1A4BA8;
  --india-green: #138808;
  --green-light: #20B814;
  --white: #FFFFFF;
  --bg-dark: #060B18;
  --bg-card: rgba(255,255,255,0.04);
  --bg-card-hover: rgba(255,255,255,0.08);
  --border: rgba(255,255,255,0.10);
  --border-active: rgba(255,107,0,0.5);
  --text-primary: #F0F4FF;
  --text-secondary: rgba(240,244,255,0.65);
  --text-muted: rgba(240,244,255,0.35);
  --radius-lg: 20px;
  --radius-xl: 28px;
  --radius-pill: 50px;
  --shadow-glow: 0 0 40px rgba(255,107,0,0.15);
  --transition: 0.3s cubic-bezier(0.4,0,0.2,1);
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', 'Noto Sans', sans-serif;
  background: var(--bg-dark);
  color: var(--text-primary);
  min-height: 100vh;
  overflow-x: hidden;
}
.bg-orbs { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
.orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.12; animation: drift 20s ease-in-out infinite; }
.orb-1 { width: 600px; height: 600px; background: var(--saffron); top: -200px; right: -100px; animation-delay: 0s; }
.orb-2 { width: 500px; height: 500px; background: var(--india-blue-mid); bottom: -150px; left: -100px; animation-delay: -7s; }
.orb-3 { width: 350px; height: 350px; background: var(--india-green); top: 40%; left: 40%; animation-delay: -14s; }
@keyframes drift { 0%,100%{transform:translate(0,0) scale(1)} 33%{transform:translate(40px,-40px) scale(1.08)} 66%{transform:translate(-30px,30px) scale(0.95)} }
.app { position: relative; z-index: 1; min-height: 100vh; display: flex; flex-direction: column; }
header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 32px;
  background: rgba(6,11,24,0.7);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}
.brand { display: flex; align-items: center; gap: 14px; text-decoration: none; }
.brand-logo { width: 48px; height: 48px; border-radius: 14px; overflow: hidden; border: 2px solid rgba(255,107,0,0.4); box-shadow: 0 0 20px rgba(255,107,0,0.2); }
.brand-logo img { width: 100%; height: 100%; object-fit: cover; }
.brand-logo-fallback { width: 48px; height: 48px; border-radius: 14px; background: linear-gradient(135deg,#FF6B00,#1A4BA8); display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 900; color: white; box-shadow: 0 0 20px rgba(255,107,0,0.3); }
.brand-text h1 { font-size: 22px; font-weight: 800; letter-spacing: -0.5px; background: linear-gradient(135deg,#FF6B00,#FFB347); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.brand-text p { font-size: 11px; color: var(--text-muted); letter-spacing: 0.5px; margin-top: 1px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.lang-pills { display: flex; gap: 8px; }
.lang-pill { padding: 6px 14px; border-radius: var(--radius-pill); border: 1px solid var(--border); background: var(--bg-card); color: var(--text-secondary); font-size: 12px; font-weight: 600; cursor: pointer; transition: var(--transition); }
.lang-pill.active, .lang-pill:hover { border-color: var(--saffron); color: var(--saffron); background: var(--saffron-glow); }
.status-dot { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-muted); }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; animation: pulse-dot 2s infinite; }
.dot.offline { background: #f87171; animation: none; }
@keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.3)} }
.hero { text-align: center; padding: 60px 24px 40px; }
.hero-badge { display: inline-flex; align-items: center; gap: 8px; background: rgba(255,107,0,0.1); border: 1px solid rgba(255,107,0,0.3); border-radius: var(--radius-pill); padding: 8px 20px; font-size: 13px; color: var(--saffron); font-weight: 600; margin-bottom: 24px; }
.hero h2 { font-size: clamp(28px,5vw,52px); font-weight: 900; line-height: 1.1; letter-spacing: -1px; margin-bottom: 16px; }
.hero h2 span { background: linear-gradient(135deg,#FF6B00,#FFB347,#FF6B00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero p { font-size: 16px; color: var(--text-secondary); max-width: 560px; margin: 0 auto 32px; line-height: 1.7; }
.flags { display: flex; justify-content: center; gap: 16px; margin-bottom: 8px; }
.flag-item { display: flex; align-items: center; gap: 6px; font-size: 14px; color: var(--text-secondary); }
.main-container { max-width: 860px; margin: 0 auto; padding: 0 24px 60px; width: 100%; }
.chat-card { background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: var(--radius-xl); backdrop-filter: blur(20px); overflow: hidden; box-shadow: 0 20px 80px rgba(0,0,0,0.4), var(--shadow-glow); }
.messages { min-height: 340px; max-height: 520px; overflow-y: auto; padding: 28px; display: flex; flex-direction: column; gap: 16px; scroll-behavior: smooth; }
.messages::-webkit-scrollbar { width: 4px; }
.messages::-webkit-scrollbar-track { background: transparent; }
.messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
.msg { display: flex; gap: 12px; animation: msg-in 0.4s ease; }
.msg.user { flex-direction: row-reverse; }
@keyframes msg-in { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
.msg-avatar { width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 700; }
.msg.dhvaani .msg-avatar { background: linear-gradient(135deg,#FF6B00,#FF8C38); color: white; font-size: 14px; }
.msg.user .msg-avatar { background: linear-gradient(135deg,#1A4BA8,#0A2E6E); color: white; font-size: 14px; }
.msg-bubble { max-width: 76%; padding: 14px 18px; border-radius: 18px; line-height: 1.6; font-size: 14px; }
.msg.dhvaani .msg-bubble { background: rgba(255,107,0,0.08); border: 1px solid rgba(255,107,0,0.15); border-bottom-left-radius: 4px; }
.msg.user .msg-bubble { background: rgba(26,75,168,0.15); border: 1px solid rgba(26,75,168,0.25); border-bottom-right-radius: 4px; text-align: right; }
.msg-bubble .lang-tag { display: inline-block; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; margin-bottom: 6px; background: rgba(255,107,0,0.2); color: var(--saffron); letter-spacing: 0.5px; }
/* ── TRANSCRIPT BOX (Phase 2) ── */
.transcript-box { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; padding: 12px 16px; margin: 6px 0; text-align: left; }
.transcript-label { font-size: 10px; font-weight: 700; letter-spacing: 1px; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; }
.transcript-text { font-size: 14px; color: var(--text-primary); line-height: 1.6; font-style: italic; }
/* ── TTS CONTROLS (Phase 2) ── */
.tts-controls { display: flex; align-items: center; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
.tts-btn { display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px; border-radius: var(--radius-pill); border: 1px solid rgba(255,107,0,0.3); background: rgba(255,107,0,0.08); color: var(--saffron); font-size: 12px; font-weight: 600; cursor: pointer; transition: var(--transition); white-space: nowrap; }
.tts-btn:hover { background: rgba(255,107,0,0.18); border-color: var(--saffron); transform: translateY(-1px); }
.tts-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
.tts-btn.stop-btn { background: rgba(248,113,113,0.08); border-color: rgba(248,113,113,0.3); color: #f87171; }
.tts-btn.stop-btn:hover { background: rgba(248,113,113,0.18); }
/* ── RESULT CARDS ── */
.result-card { background: rgba(255,255,255,0.04); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; margin-top: 12px; transition: var(--transition); }
.result-card:hover { border-color: rgba(255,107,0,0.3); background: rgba(255,107,0,0.03); }
.result-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.result-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.scheme-icon { background: rgba(19,136,8,0.15); }
.grievance-icon { background: rgba(255,107,0,0.15); }
.result-title { font-weight: 700; font-size: 15px; }
.result-subtitle { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.eligibility-list { list-style: none; }
.eligibility-list li { display: flex; align-items: flex-start; gap: 8px; padding: 6px 0; font-size: 13px; color: var(--text-secondary); border-bottom: 1px solid rgba(255,255,255,0.04); }
.eligibility-list li:last-child { border-bottom: none; }
.eligibility-list li::before { content: "✓"; color: var(--green-light); font-weight: 700; flex-shrink: 0; margin-top: 1px; }
.steps-list { list-style: none; counter-reset: steps; }
.steps-list li { counter-increment: steps; display: flex; align-items: flex-start; gap: 10px; padding: 8px 0; font-size: 13px; color: var(--text-secondary); }
.steps-list li::before { content: counter(steps); background: rgba(255,107,0,0.2); color: var(--saffron); min-width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.benefit-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(19,136,8,0.1); border: 1px solid rgba(19,136,8,0.25); border-radius: var(--radius-pill); padding: 6px 14px; font-size: 13px; color: #4ade80; font-weight: 600; margin: 10px 0; }
.helpline-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(26,75,168,0.1); border: 1px solid rgba(26,75,168,0.25); border-radius: var(--radius-pill); padding: 6px 14px; font-size: 12px; color: #93c5fd; font-weight: 500; }
.section-label { font-size: 11px; font-weight: 700; letter-spacing: 1px; color: var(--text-muted); text-transform: uppercase; margin: 14px 0 8px; }
.grievance-draft { background: rgba(255,107,0,0.05); border: 1px solid rgba(255,107,0,0.2); border-radius: 12px; padding: 16px; margin: 12px 0; font-size: 14px; line-height: 1.7; color: var(--text-primary); }
.grievance-meta { display: flex; flex-wrap: wrap; gap: 10px; margin: 12px 0; }
.meta-chip { padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.priority-urgent { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }
.priority-high { background: rgba(255,107,0,0.15); color: var(--saffron); border: 1px solid rgba(255,107,0,0.3); }
.priority-medium { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.dept-chip { background: rgba(26,75,168,0.15); color: #93c5fd; border: 1px solid rgba(26,75,168,0.3); }
.confirm-row { display: flex; gap: 12px; margin-top: 16px; }
.btn-confirm { flex: 1; padding: 14px; border-radius: 12px; border: none; cursor: pointer; font-weight: 700; font-size: 14px; transition: var(--transition); display: flex; align-items: center; justify-content: center; gap: 8px; }
.btn-yes { background: linear-gradient(135deg,#138808,#20B814); color: white; box-shadow: 0 4px 20px rgba(19,136,8,0.3); }
.btn-yes:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(19,136,8,0.4); }
.btn-no { background: rgba(248,113,113,0.1); color: #f87171; border: 1px solid rgba(248,113,113,0.3); }
.btn-no:hover { background: rgba(248,113,113,0.2); }
.tracking-card { background: linear-gradient(135deg,rgba(19,136,8,0.08),rgba(20,184,20,0.05)); border: 1px solid rgba(19,136,8,0.3); border-radius: 16px; padding: 20px; margin: 12px 0; }
.tracking-id { font-size: 22px; font-weight: 900; color: #4ade80; letter-spacing: 2px; margin: 8px 0; font-family: monospace; }
.tracking-steps li { padding: 6px 0; font-size: 13px; color: var(--text-secondary); display: flex; gap: 8px; }
.tracking-steps li::before { content: "→"; color: var(--green-light); flex-shrink: 0; }
.suggestions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.suggestion-chip { padding: 8px 14px; border-radius: var(--radius-pill); border: 1px solid var(--border); background: var(--bg-card); color: var(--text-secondary); font-size: 13px; cursor: pointer; transition: var(--transition); }
.suggestion-chip:hover { border-color: var(--saffron); color: var(--saffron); background: var(--saffron-glow); transform: translateY(-2px); }
.typing { display: flex; align-items: center; gap: 6px; padding: 10px 0; }
.typing span { width: 8px; height: 8px; border-radius: 50%; background: var(--saffron); animation: bounce 1.2s ease-in-out infinite; }
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-8px)} }
/* ── VOICE STATE PANEL (Phase 2) ── */
.voice-state-panel { display: none; align-items: center; gap: 12px; padding: 12px 20px; background: rgba(255,107,0,0.06); border-top: 1px solid rgba(255,107,0,0.12); }
.voice-state-panel.visible { display: flex; }
.voice-state-icon { font-size: 22px; flex-shrink: 0; }
.voice-state-text { flex: 1; }
.voice-state-label { font-size: 13px; font-weight: 700; color: var(--text-primary); }
.voice-state-sublabel { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.voice-wave { display: flex; align-items: center; gap: 3px; height: 24px; }
.voice-wave span { width: 3px; border-radius: 2px; background: var(--saffron); opacity: 0.7; animation: wave-bar 0.8s ease-in-out infinite; }
.voice-wave span:nth-child(1) { height: 8px; animation-delay: 0s; }
.voice-wave span:nth-child(2) { height: 16px; animation-delay: 0.1s; }
.voice-wave span:nth-child(3) { height: 24px; animation-delay: 0.2s; }
.voice-wave span:nth-child(4) { height: 16px; animation-delay: 0.3s; }
.voice-wave span:nth-child(5) { height: 10px; animation-delay: 0.4s; }
@keyframes wave-bar { 0%,100%{transform:scaleY(0.4)} 50%{transform:scaleY(1)} }
/* ── INPUT AREA ── */
.input-area { padding: 20px 28px; border-top: 1px solid var(--border); background: rgba(6,11,24,0.5); backdrop-filter: blur(10px); }
.input-row { display: flex; gap: 12px; align-items: flex-end; }
.text-input-wrap { flex: 1; position: relative; }
#text-input { width: 100%; background: rgba(255,255,255,0.05); border: 1.5px solid var(--border); border-radius: 16px; padding: 14px 20px; color: var(--text-primary); font-size: 15px; font-family: inherit; resize: none; outline: none; min-height: 52px; max-height: 120px; transition: var(--transition); line-height: 1.5; }
#text-input:focus { border-color: var(--saffron); box-shadow: 0 0 0 3px rgba(255,107,0,0.1); }
#text-input::placeholder { color: var(--text-muted); }
.char-count { position: absolute; bottom: 8px; right: 12px; font-size: 10px; color: var(--text-muted); }
.action-btns { display: flex; gap: 10px; align-items: center; }
/* ── MIC BUTTON STATES (Phase 2) ── */
.mic-wrap { position: relative; display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0; }
#record-btn { width: 56px; height: 56px; border-radius: 50%; border: none; cursor: pointer; background: linear-gradient(135deg,var(--india-blue-mid),var(--india-blue)); color: white; font-size: 22px; display: flex; align-items: center; justify-content: center; transition: var(--transition); box-shadow: 0 4px 20px rgba(26,75,168,0.4); position: relative; touch-action: manipulation; -webkit-tap-highlight-color: transparent; }
#record-btn:hover:not(:disabled) { transform: scale(1.08); }
#record-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
#record-btn.state-listening { background: linear-gradient(135deg,#ef4444,#dc2626); animation: record-pulse 1.2s infinite; }
@keyframes record-pulse { 0%{box-shadow:0 0 0 0 rgba(239,68,68,0.4)} 70%{box-shadow:0 0 0 16px rgba(239,68,68,0)} 100%{box-shadow:0 0 0 0 rgba(239,68,68,0)} }
#record-btn.state-listening .record-ring { display: block; }
#record-btn.state-processing { background: linear-gradient(135deg,#d97706,#b45309); animation: amber-glow 1.5s ease-in-out infinite; }
@keyframes amber-glow { 0%,100%{box-shadow:0 0 0 0 rgba(217,119,6,0.5)} 50%{box-shadow:0 0 20px 4px rgba(217,119,6,0.3)} }
#record-btn.state-speaking { background: linear-gradient(135deg,#059669,#047857); animation: speak-pulse 1s ease-in-out infinite; }
@keyframes speak-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(5,150,105,0.5)} 50%{box-shadow:0 0 0 12px rgba(5,150,105,0)} }
.record-ring { position: absolute; inset: -4px; border-radius: 50%; border: 2px solid rgba(239,68,68,0.5); animation: record-ring 1.2s infinite; display: none; }
@keyframes record-ring { 0%{transform:scale(1);opacity:1} 100%{transform:scale(1.4);opacity:0} }
.mic-state-label { font-size: 10px; font-weight: 700; letter-spacing: 0.5px; color: var(--text-muted); text-transform: uppercase; text-align: center; white-space: nowrap; transition: var(--transition); }
#send-btn { height: 56px; padding: 0 24px; border-radius: 16px; border: none; cursor: pointer; background: linear-gradient(135deg,var(--saffron),var(--saffron-light)); color: white; font-size: 15px; font-weight: 700; font-family: inherit; transition: var(--transition); box-shadow: 0 4px 20px rgba(255,107,0,0.3); white-space: nowrap; flex-shrink: 0; }
#send-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(255,107,0,0.4); }
#send-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.input-hints { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
.hint-text { font-size: 12px; color: var(--text-muted); }
.hint-text.listening { color: #ef4444; font-weight: 600; }
.hint-text.processing { color: #d97706; font-weight: 600; }
.hint-text.speaking { color: #059669; font-weight: 600; }
/* ── FEATURES STRIP ── */
.features-strip { display: flex; gap: 0; justify-content: center; align-items: stretch; border: 1px solid var(--border); border-radius: var(--radius-xl); overflow: hidden; margin: 32px 0; background: var(--bg-card); }
.feature-item { flex: 1; padding: 24px 20px; text-align: center; border-right: 1px solid var(--border); transition: var(--transition); }
.feature-item:last-child { border-right: none; }
.feature-item:hover { background: var(--bg-card-hover); }
.feature-icon { font-size: 28px; margin-bottom: 10px; }
.feature-title { font-size: 14px; font-weight: 700; margin-bottom: 4px; }
.feature-desc { font-size: 12px; color: var(--text-muted); line-height: 1.5; }
/* ── API BANNER ── */
.api-banner { background: rgba(255,107,0,0.08); border: 1px solid rgba(255,107,0,0.25); border-radius: 12px; padding: 14px 20px; margin-bottom: 20px; display: flex; align-items: center; gap: 14px; font-size: 13px; color: var(--text-secondary); }
.api-banner strong { color: var(--saffron); }
.api-banner a { color: var(--saffron); text-decoration: underline; }
.api-input-row { display: flex; gap: 10px; margin-top: 10px; }
.api-key-input { flex: 1; background: rgba(255,255,255,0.05); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; color: var(--text-primary); font-size: 13px; outline: none; font-family: monospace; }
.api-key-input:focus { border-color: var(--saffron); }
.btn-save-key { padding: 10px 20px; border-radius: 10px; border: none; cursor: pointer; background: var(--saffron); color: white; font-weight: 700; font-size: 13px; transition: var(--transition); }
.btn-save-key:hover { background: var(--saffron-light); }
/* ── TOAST ── */
.toast { position: fixed; bottom: 24px; right: 24px; z-index: 999; background: rgba(6,11,24,0.95); border: 1px solid var(--border); border-radius: 12px; padding: 14px 20px; font-size: 14px; backdrop-filter: blur(20px); display: none; animation: toast-in 0.3s ease; max-width: 320px; }
.toast.success { border-color: rgba(74,222,128,0.4); color: #4ade80; }
.toast.error { border-color: rgba(248,113,113,0.4); color: #f87171; }
.toast.info { border-color: rgba(255,107,0,0.4); color: var(--saffron); }
@keyframes toast-in { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
/* ── DEBUG PANEL ── */
.debug-panel { display: none; margin-top: 12px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 12px 16px; font-size: 11px; font-family: monospace; color: var(--text-muted); line-height: 1.8; }
.debug-panel.visible { display: block; }
.debug-row { display: flex; gap: 8px; }
.debug-key { color: rgba(255,107,0,0.7); min-width: 120px; }
.debug-val { color: #94a3b8; }
footer { text-align: center; padding: 24px; border-top: 1px solid var(--border); color: var(--text-muted); font-size: 12px; line-height: 1.8; background: rgba(6,11,24,0.5); }
footer a { color: var(--text-muted); }
@media (max-width: 640px) {
  header { padding: 14px 16px; }
  .brand-text p { display: none; }
  .lang-pills { gap: 6px; }
  .lang-pill { padding: 5px 10px; font-size: 11px; }
  .features-strip { flex-direction: column; }
  .feature-item { border-right: none; border-bottom: 1px solid var(--border); }
  .feature-item:last-child { border-bottom: none; }
  .input-row { gap: 8px; }
  #send-btn { padding: 0 14px; font-size: 13px; }
  #record-btn { width: 52px; height: 52px; }
  .confirm-row { flex-direction: column; }
  .tts-controls { gap: 6px; }
}
</style>
</head>
<body>
<div class="bg-orbs">
  <div class="orb orb-1"></div>
  <div class="orb orb-2"></div>
  <div class="orb orb-3"></div>
</div>
<div class="app">
  <header>
    <div class="brand">
      <div class="brand-logo" id="logo-container">
        <img src="/static/logo.jpg" alt="Dhvaani" id="brand-logo-img">
      </div>
      <div class="brand-text">
        <h1>Dhvaani</h1>
        <p>MULTILINGUAL GOVERNMENT ASSISTANT</p>
      </div>
    </div>
    <div class="header-right">
      <div class="lang-pills">
        <button class="lang-pill active" id="lang-en" onclick="setLang('en')">&#127468;&#127463; English</button>
        <button class="lang-pill" id="lang-hi" onclick="setLang('hi')">&#127470;&#127475; &#2361;&#2367;&#2306;&#2342;&#2368;</button>
        <button class="lang-pill" id="lang-ta" onclick="setLang('ta')">&#127470;&#127475; &#2980;&#2990;&#3007;&#2996;&#3021;</button>
      </div>
      <div class="status-dot">
        <div class="dot" id="status-dot"></div>
        <span id="status-text">Connecting...</span>
      </div>
    </div>
  </header>
  <section class="hero">
    <div class="hero-badge">&#127897;&#65039; Speak. Understand. Act.</div>
    <h2>Government Services<br><span>In Your Language</span></h2>
    <p>Simply speak in Tamil, Hindi, or English. Dhvaani understands, finds relevant schemes, and helps file grievances &mdash; <em>no forms needed.</em></p>
    <div class="flags">
      <div class="flag-item">&#127470;&#127475; Tamil</div>
      <div class="flag-item">&bull;</div>
      <div class="flag-item">&#127470;&#127475; Hindi</div>
      <div class="flag-item">&bull;</div>
      <div class="flag-item">&#127468;&#127463; English</div>
    </div>
  </section>
  <main class="main-container">
    <div class="api-banner" id="api-banner" style="display:none">
      <div style="font-size:24px">&#128273;</div>
      <div style="flex:1">
        <strong>Add your Gemini API Key</strong> to enable AI features (voice transcription, smart responses).<br>
        <a href="https://aistudio.google.com/app/apikey" target="_blank">Get a free key at Google AI Studio &rarr;</a>
        <div class="api-input-row">
          <input type="password" class="api-key-input" id="api-key-input" placeholder="AIza...">
          <button class="btn-save-key" onclick="saveApiKey()">Save Key</button>
        </div>
      </div>
    </div>
    <div class="features-strip">
      <div class="feature-item">
        <div class="feature-icon">&#127897;&#65039;</div>
        <div class="feature-title">Voice Input</div>
        <div class="feature-desc">Speak naturally in any language</div>
      </div>
      <div class="feature-item">
        <div class="feature-icon">&#128266;</div>
        <div class="feature-title">Voice Output</div>
        <div class="feature-desc">Dhvaani speaks back in your language</div>
      </div>
      <div class="feature-item">
        <div class="feature-icon">&#127963;&#65039;</div>
        <div class="feature-title">12+ Schemes</div>
        <div class="feature-desc">PM-KISAN, Ayushman, NREGA &amp; more</div>
      </div>
      <div class="feature-item">
        <div class="feature-icon">&#128203;</div>
        <div class="feature-title">Smart Grievance</div>
        <div class="feature-desc">Routes to the right department</div>
      </div>
    </div>
    <div class="chat-card">
      <div class="messages" id="messages">
        <div class="msg dhvaani" id="welcome-msg">
          <div class="msg-avatar">&#2343;</div>
          <div class="msg-bubble">
            <span class="lang-tag">DHVAANI</span>
            <p>&#128075; Namaste! I am <strong>Dhvaani</strong>, your multilingual government services assistant.</p>
            <p style="margin-top:8px">I can help you with:</p>
            <ul style="margin:8px 0 8px 16px;color:var(--text-secondary);font-size:13px;line-height:1.8">
              <li>&#127963;&#65039; <strong>Find government schemes</strong> you may be eligible for</li>
              <li>&#128203; <strong>File grievances</strong> about civic issues (lights, roads, water...)</li>
            </ul>
            <p style="font-size:13px;color:var(--text-secondary)">Just <strong>tap the microphone</strong> and speak in Tamil, Hindi, or English!</p>
            <div class="suggestions" style="margin-top:14px">
              <button class="suggestion-chip" onclick="useSuggestion(this.textContent)">Am I eligible for PM-KISAN?</button>
              <button class="suggestion-chip" onclick="useSuggestion(this.textContent)">Street light not working</button>
              <button class="suggestion-chip" onclick="useSuggestion(this.textContent)">Ayushman Bharat eligibility</button>
              <button class="suggestion-chip" onclick="useSuggestion(this.textContent)">Road has potholes</button>
            </div>
          </div>
        </div>
      </div>
      <!-- VOICE STATE PANEL -->
      <div class="voice-state-panel" id="voice-state-panel">
        <div class="voice-state-icon" id="voice-state-icon">&#127897;&#65039;</div>
        <div class="voice-state-text">
          <div class="voice-state-label" id="voice-state-label">Tap to speak</div>
          <div class="voice-state-sublabel" id="voice-state-sublabel">Ready</div>
        </div>
        <div class="voice-wave" id="voice-wave">
          <span></span><span></span><span></span><span></span><span></span>
        </div>
      </div>
      <!-- INPUT AREA -->
      <div class="input-area">
        <div class="input-row">
          <div class="text-input-wrap">
            <textarea id="text-input" placeholder="Type your question or use the mic to speak..." rows="1" maxlength="600" oninput="autoResize(this);updateCharCount(this)"></textarea>
            <span class="char-count" id="char-count">0/600</span>
          </div>
          <div class="action-btns">
            <div class="mic-wrap">
              <button id="record-btn" title="Tap to speak" onclick="toggleRecording()">
                &#127897;&#65039;
                <div class="record-ring"></div>
              </button>
              <span class="mic-state-label" id="mic-state-label">TAP TO SPEAK</span>
            </div>
            <button id="send-btn" onclick="sendMessage()">Send &rarr;</button>
          </div>
        </div>
        <div class="input-hints">
          <span class="hint-text" id="hint-text">&#127760; Language auto-detected &bull; Supports Tamil, Hindi, English</span>
          <span style="font-size:11px;color:var(--text-muted);cursor:pointer" onclick="toggleDebug()" title="Toggle debug panel">&#9881;&#65039;</span>
        </div>
        <div class="debug-panel" id="debug-panel">
          <div class="debug-row"><span class="debug-key">lang_selected:</span><span class="debug-val" id="dbg-lang">en</span></div>
          <div class="debug-row"><span class="debug-key">lang_detected:</span><span class="debug-val" id="dbg-lang-det">-</span></div>
          <div class="debug-row"><span class="debug-key">transcript:</span><span class="debug-val" id="dbg-transcript">-</span></div>
          <div class="debug-row"><span class="debug-key">tts_status:</span><span class="debug-val" id="dbg-tts">idle</span></div>
          <div class="debug-row"><span class="debug-key">tts_voice:</span><span class="debug-val" id="dbg-voice">-</span></div>
          <div class="debug-row"><span class="debug-key">intent:</span><span class="debug-val" id="dbg-intent">-</span></div>
          <div class="debug-row"><span class="debug-key">mic_state:</span><span class="debug-val" id="dbg-mic">idle</span></div>
        </div>
      </div>
    </div>
  </main>
  <footer>
    <p>&#127470;&#127475; <strong>Dhvaani</strong> &mdash; Reducing 25-minute government visits to under 2 minutes</p>
    <p style="margin-top:4px">Built for rural citizens, farmers, daily-wage workers &amp; elderly pensioners</p>
    <p style="margin-top:4px;font-size:11px">Powered by Google Gemini AI &bull; <a href="https://pgportal.gov.in" target="_blank">CPGRAMS Portal</a> &bull; <a href="https://pmkisan.gov.in" target="_blank">PM-KISAN</a></p>
  </footer>
</div>
<div class="toast" id="toast"></div>
<script>
// ═══════════════════════════════════════════
// DHVAANI PHASE 2 — VOICE-FIRST FRONTEND
// ═══════════════════════════════════════════
const API_BASE = '';

// ── Multilingual UI strings ──
const LS = {
  en: {
    tap:'TAP TO SPEAK', listen:'Listening...', process:'Understanding...', speak:'Speaking...',
    err:'Something went wrong. Try again.', ok:'Here\'s what I found.',
    you_said:'You said', listen_btn:'▶ Listen', replay_btn:'↻ Replay', stop_btn:'⏹ Stop',
    ph:'Type your question or use the mic to speak...',
    no_audio:'I couldn\'t hear anything. Please try speaking again.',
    xfail:'I couldn\'t understand the audio. Please speak clearly.',
    mic_deny:'Microphone access is needed for voice input.',
    type_it:'Type instead', try_again:'Try Again',
    hint:'🌐 Language auto-detected • Supports Tamil, Hindi, English',
  },
  hi: {
    tap:'बोलने के लिए टैप करें', listen:'सुन रहा हूँ...', process:'समझ रहा हूँ...', speak:'बोल रहा हूँ...',
    err:'कुछ गलत हुआ। फिर से कोशिश करें।', ok:'यह रहा जवाब।',
    you_said:'आपने कहा', listen_btn:'▶ सुनें', replay_btn:'↻ फिर सुनें', stop_btn:'⏹ रोकें',
    ph:'अपना प्रश्न टाइप करें या माइक से बोलें...',
    no_audio:'मैं कुछ सुन नहीं पाया। कृपया फिर से बोलें।',
    xfail:'ऑडियो समझ नहीं आया। कृपया स्पष्ट रूप से बोलें।',
    mic_deny:'माइक्रोफोन की अनुमति चाहिए।',
    type_it:'टाइप करें', try_again:'फिर से कोशिश करें',
    hint:'🌐 भाषा स्वतः पहचानी जाती है • Tamil, Hindi, English',
  },
  ta: {
    tap:'பேச தொடங்க தட்டவும்', listen:'கேட்கிறேன்...', process:'புரிந்துகொள்கிறேன்...', speak:'பேசுகிறேன்...',
    err:'தவறு நேர்ந்தது. மீண்டும் முயலுங்கள்.', ok:'இதோ பதில்.',
    you_said:'நீங்கள் சொன்னது', listen_btn:'▶ கேளுங்கள்', replay_btn:'↻ மீண்டும் கேளுங்கள்', stop_btn:'⏹ நிறுத்து',
    ph:'உங்கள் கேள்வியை தட்டச்சு செய்யுங்கள் அல்லது மைக்கில் பேசுங்கள்...',
    no_audio:'ஒலி கேட்கவில்லை. மீண்டும் பேசுங்கள்.',
    xfail:'ஆடியோ புரியவில்லை. தெளிவாக பேசுங்கள்.',
    mic_deny:'குரல் உள்ளீட்டுக்கு மைக்ரோஃபோன் அனுமதி தேவை.',
    type_it:'தட்டச்சு செய்யுங்கள்', try_again:'மீண்டும் முயலுங்கள்',
    hint:'🌐 மொழி தானாக கண்டறியப்படுகிறது • Tamil, Hindi, English',
  }
};
function T(k) { return (LS[S.lang]||LS.en)[k] || (LS.en[k] || k); }

// ── State ──
const S = {
  lang:'en', micState:'idle', recording:false,
  mediaRecorder:null, audioChunks:[],
  pendingGrievanceId:null,
  apiKey: localStorage.getItem('dhvaani_api_key')||'',
  ttsOk: 'speechSynthesis' in window,
  voices:[], lastText:'', lastLang:'en',
  debugOn:false, ttsCounter:0,
};

// ── Init ──
document.addEventListener('DOMContentLoaded', async ()=>{
  const li = document.getElementById('brand-logo-img');
  if(li) li.onerror = function(){ this.parentElement.innerHTML='<div class="brand-logo-fallback">&#2343;</div>'; };
  await checkHealth();
  if(!S.apiKey) document.getElementById('api-banner').style.display='flex';
  document.getElementById('text-input').addEventListener('keydown', e=>{
    if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();}
  });
  if(S.ttsOk){
    S.voices = window.speechSynthesis.getVoices();
    if(window.speechSynthesis.onvoiceschanged !== undefined)
      window.speechSynthesis.onvoiceschanged = ()=>{ S.voices=window.speechSynthesis.getVoices(); };
  }
  setMicState('idle');
});

async function checkHealth(){
  try{
    const r=await fetch('/api/health'); const d=await r.json();
    const dot=document.getElementById('status-dot'); const tx=document.getElementById('status-text');
    if(d.status==='online'){ dot.classList.remove('offline'); tx.textContent=d.gemini_configured?'AI Ready':'Online (No API Key)'; }
    else{ dot.classList.add('offline'); tx.textContent='Offline'; }
  }catch(e){ document.getElementById('status-dot').classList.add('offline'); document.getElementById('status-text').textContent='Offline'; }
}

function setLang(l){
  S.lang=l;
  ['en','hi','ta'].forEach(x=>document.getElementById('lang-'+x).classList.toggle('active',x===l));
  document.getElementById('text-input').placeholder=T('ph');
  document.getElementById('hint-text').textContent=T('hint');
  setMicState(S.micState);
  dbg('dbg-lang',l);
}

function saveApiKey(){
  const k=document.getElementById('api-key-input').value.trim();
  if(!k.startsWith('AIza')){showToast('Invalid key format','error');return;}
  S.apiKey=k; localStorage.setItem('dhvaani_api_key',k);
  fetch('/api/set-key',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:k})}).catch(()=>{});
  document.getElementById('api-banner').style.display='none';
  showToast('API Key saved! AI features enabled.','success'); checkHealth();
}

// ═══════════════════════════════════════
// MIC STATE MACHINE
// ═══════════════════════════════════════
function setMicState(ns){
  S.micState=ns;
  const btn=document.getElementById('record-btn');
  const lbl=document.getElementById('mic-state-label');
  const hint=document.getElementById('hint-text');
  const panel=document.getElementById('voice-state-panel');
  const pIcon=document.getElementById('voice-state-icon');
  const pLbl=document.getElementById('voice-state-label');
  const pSub=document.getElementById('voice-state-sublabel');
  const wave=document.getElementById('voice-wave');
  btn.classList.remove('state-listening','state-processing','state-speaking');
  hint.className='hint-text';
  switch(ns){
    case 'idle':
      btn.innerHTML='&#127897;&#65039;<div class="record-ring"></div>';
      btn.disabled=false; lbl.textContent=T('tap');
      hint.textContent=T('hint'); panel.classList.remove('visible'); break;
    case 'listening':
      btn.classList.add('state-listening');
      btn.innerHTML='&#9209;&#65039;<div class="record-ring"></div>';
      btn.disabled=false; lbl.textContent=T('listen');
      hint.className='hint-text listening';
      hint.textContent='🔴 '+T('listen')+' — tap ⏹ to stop';
      panel.classList.add('visible');
      pIcon.innerHTML='&#127897;&#65039;'; pLbl.textContent=T('listen');
      pSub.textContent='Speak clearly into your microphone';
      wave.style.display='flex'; break;
    case 'processing':
      btn.classList.add('state-processing');
      btn.innerHTML='&#9203;<div class="record-ring"></div>';
      btn.disabled=true; lbl.textContent=T('process');
      hint.className='hint-text processing'; hint.textContent='⏳ '+T('process');
      panel.classList.add('visible');
      pIcon.textContent='🧠'; pLbl.textContent=T('process');
      pSub.textContent='Dhvaani is understanding your request';
      wave.style.display='none'; break;
    case 'speaking':
      btn.classList.add('state-speaking');
      btn.innerHTML='&#128266;<div class="record-ring"></div>';
      btn.disabled=true; lbl.textContent=T('speak');
      hint.className='hint-text speaking'; hint.textContent='🔊 '+T('speak');
      panel.classList.add('visible');
      pIcon.innerHTML='&#128266;'; pLbl.textContent=T('speak');
      pSub.textContent='Dhvaani is reading the response';
      wave.style.display='flex'; break;
    case 'error':
      btn.innerHTML='&#127897;&#65039;<div class="record-ring"></div>';
      btn.disabled=false; lbl.textContent=T('err');
      hint.textContent=T('err'); panel.classList.remove('visible'); break;
    case 'success':
      btn.innerHTML='&#127897;&#65039;<div class="record-ring"></div>';
      btn.disabled=false; lbl.textContent=T('tap');
      hint.textContent=T('hint'); panel.classList.remove('visible'); break;
  }
  dbg('dbg-mic',ns);
}

// ═══════════════════════════════════════
// VOICE RECORDING
// ═══════════════════════════════════════
async function toggleRecording(){
  if(S.micState==='listening') stopRec();
  else if(['idle','error','success'].includes(S.micState)) await startRec();
}

async function startRec(){
  stopSpeech();
  try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
    S.audioChunks=[];
    const opts=MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?{mimeType:'audio/webm;codecs=opus'}:
                MediaRecorder.isTypeSupported('audio/webm')?{mimeType:'audio/webm'}:{};
    S.mediaRecorder=new MediaRecorder(stream,opts);
    S.mediaRecorder.ondataavailable=e=>{if(e.data.size>0)S.audioChunks.push(e.data);};
    S.mediaRecorder.onstop=processRec;
    S.mediaRecorder.start(200); S.recording=true; setMicState('listening');
  }catch(err){
    console.error('[Dhvaani] Mic:',err.name,err.message);
    if(err.name==='NotAllowedError'||err.name==='PermissionDeniedError'){
      addBot('<p>🚫 '+esc(T('mic_deny'))+'</p><p style="font-size:13px;color:var(--text-muted);margin-top:6px">Allow microphone access in your browser settings.</p>'
        +'<div class="suggestions" style="margin-top:10px"><button class="suggestion-chip" onclick="document.getElementById(\'text-input\').focus()">⌨️ '+esc(T('type_it'))+'</button></div>');
    }else{ showToast('Microphone error: '+err.message,'error'); }
    setMicState('error');
  }
}

function stopRec(){
  if(S.mediaRecorder&&S.recording){
    S.mediaRecorder.stop();
    S.mediaRecorder.stream.getTracks().forEach(t=>t.stop());
    S.recording=false; setMicState('processing');
  }
}

async function processRec(){
  const mime=S.mediaRecorder?.mimeType||'audio/webm';
  const blob=new Blob(S.audioChunks,{type:mime});
  if(blob.size<100){
    addBot('<p>🔇 '+esc(T('no_audio'))+'</p>'
      +'<div class="suggestions" style="margin-top:10px">'
      +'<button class="suggestion-chip" onclick="toggleRecording()">🎙️ '+esc(T('try_again'))+'</button>'
      +'<button class="suggestion-chip" onclick="document.getElementById(\'text-input\').focus()">⌨️ '+esc(T('type_it'))+'</button>'
      +'</div>');
    setMicState('idle'); return;
  }
  addTyping();
  const fd=new FormData();
  fd.append('audio',blob,'recording.webm');
  fd.append('language',S.lang);
  try{
    const r=await fetch('/api/transcribe',{method:'POST',body:fd});
    const d=await r.json(); removeTyping();
    if(d.success&&d.transcript){
      const tx=d.transcript.trim(); dbg('dbg-transcript',tx.substring(0,50));
      addUserTranscript(tx);
      const ti=document.getElementById('text-input');
      ti.value=tx; autoResize(ti); updateCC(ti);
      await processText(tx);
    }else{
      addBot('<p>🎤 '+esc(T('xfail'))+'</p>'
        +'<div class="suggestions" style="margin-top:10px">'
        +'<button class="suggestion-chip" onclick="toggleRecording()">🎙️ '+esc(T('try_again'))+'</button>'
        +'<button class="suggestion-chip" onclick="document.getElementById(\'text-input\').focus()">⌨️ '+esc(T('type_it'))+'</button>'
        +'</div>');
      showToast(d.message||T('xfail'),'error'); setMicState('idle');
    }
  }catch(e){
    removeTyping(); console.error('[Dhvaani] Transcribe error:',e);
    addBot('<p>⚠️ '+esc(T('xfail'))+'</p>'
      +'<div class="suggestions" style="margin-top:10px">'
      +'<button class="suggestion-chip" onclick="toggleRecording()">🎙️ '+esc(T('try_again'))+'</button>'
      +'<button class="suggestion-chip" onclick="document.getElementById(\'text-input\').focus()">⌨️ '+esc(T('type_it'))+'</button>'
      +'</div>');
    setMicState('idle');
  }
}

// ═══════════════════════════════════════
// TEXT SEND
// ═══════════════════════════════════════
async function sendMessage(){
  const inp=document.getElementById('text-input');
  const tx=inp.value.trim(); if(!tx) return;
  stopSpeech(); addUserMsg(tx); inp.value=''; autoResize(inp); updateCC(inp);
  await processText(tx);
}
function useSuggestion(tx){ stopSpeech(); document.getElementById('text-input').value=tx; autoResize(document.getElementById('text-input')); sendMessage(); }

async function processText(tx){
  setMicState('processing'); addTyping();
  try{
    const r=await fetch('/api/process',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:tx,language:S.lang})});
    const d=await r.json(); removeTyping();
    if(d.language&&['en','hi','ta'].includes(d.language)){
      S.lang=d.language;
      ['en','hi','ta'].forEach(l=>document.getElementById('lang-'+l).classList.toggle('active',l===d.language));
      dbg('dbg-lang-det',d.language+(d.language_name?' ('+d.language_name+')':''));
    }
    dbg('dbg-intent',d.intent||'-');
    handleResp(d); setMicState('success');
    const ti=document.getElementById('text-input'); ti.value=''; autoResize(ti); updateCC(ti);
  }catch(e){
    removeTyping(); console.error('[Dhvaani] Process:',e);
    addBot('<p>⚠️ Dhvaani is having trouble understanding your request. Please try again.</p>');
    setMicState('error');
  }
}

// ═══════════════════════════════════════
// TTS ENGINE
// ═══════════════════════════════════════
function pickVoice(lang){
  if(!S.ttsOk) return null;
  const vs=S.voices.length?S.voices:window.speechSynthesis.getVoices();
  const m={ta:['ta-IN','ta'],hi:['hi-IN','hi'],en:['en-IN','en-GB','en-US','en']};
  const targets=m[lang]||m.en;
  for(const t of targets){ const v=vs.find(x=>x.lang.toLowerCase()===t.toLowerCase()); if(v){dbg('dbg-voice',v.name+' ('+v.lang+')');return v;} }
  for(const t of targets){ const v=vs.find(x=>x.lang.toLowerCase().startsWith(t.split('-')[0].toLowerCase())); if(v){dbg('dbg-voice',v.name+' [prefix]');return v;} }
  if(vs.length){dbg('dbg-voice',vs[0].name+' [fallback]');return vs[0];}
  dbg('dbg-voice','none'); return null;
}

function speakNow(tx,lang){
  if(!S.ttsOk||!tx) return;
  stopSpeech();
  const u=new SpeechSynthesisUtterance(tx);
  const v=pickVoice(lang||S.lang); if(v) u.voice=v;
  u.lang={en:'en-IN',hi:'hi-IN',ta:'ta-IN'}[lang||S.lang]||'en-IN';
  u.rate=0.92; u.pitch=1.0; u.volume=1.0;
  S.lastText=tx; S.lastLang=lang||S.lang;
  u.onstart=()=>{setMicState('speaking');dbg('dbg-tts','speaking');};
  u.onend=()=>{setMicState('idle');dbg('dbg-tts','done');};
  u.onerror=e=>{setMicState('idle');dbg('dbg-tts','error:'+e.error);};
  window.speechSynthesis.speak(u);
}

function stopSpeech(){
  if(S.ttsOk&&window.speechSynthesis.speaking){window.speechSynthesis.cancel();dbg('dbg-tts','stopped');}
  if(S.micState==='speaking') setMicState('idle');
}

function ttsPlay(id,lang,tx){
  const pb=document.getElementById('tp-'+id);
  const sb=document.getElementById('ts-'+id);
  const rb=document.getElementById('tr-'+id);
  if(pb) pb.style.display='none';
  if(sb) sb.style.display='inline-flex';
  if(rb) rb.style.display='none';
  const u=new SpeechSynthesisUtterance(tx);
  const v=pickVoice(lang); if(v) u.voice=v;
  u.lang={en:'en-IN',hi:'hi-IN',ta:'ta-IN'}[lang]||'en-IN';
  u.rate=0.92;
  u.onstart=()=>{setMicState('speaking');dbg('dbg-tts','card');};
  u.onend=()=>{
    setMicState('idle');
    if(pb) pb.style.display='none';
    if(sb) sb.style.display='none';
    if(rb) rb.style.display='inline-flex';
    dbg('dbg-tts','done');
  };
  u.onerror=e=>{
    setMicState('idle');
    if(pb) pb.style.display='inline-flex';
    if(sb) sb.style.display='none';
    if(rb) rb.style.display='none';
    dbg('dbg-tts','err:'+e.error);
  };
  S.lastText=tx; S.lastLang=lang;
  stopSpeech(); window.speechSynthesis.speak(u);
}

function ttsCtrl(tx,lang){
  if(!S.ttsOk||!tx) return '';
  const id='c'+(++S.ttsCounter);
  const safe=tx.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
  return '<div class="tts-controls">'
    +'<button class="tts-btn" id="tp-'+id+'" onclick="ttsPlay(\''+id+'\',\''+lang+'\',\''+safe+'\')">'+esc(T('listen_btn'))+'</button>'
    +'<button class="tts-btn stop-btn" id="ts-'+id+'" onclick="stopSpeech()" style="display:none">'+esc(T('stop_btn'))+'</button>'
    +'<button class="tts-btn" id="tr-'+id+'" onclick="ttsPlay(\''+id+'\',\''+lang+'\',\''+safe+'\')" style="display:none">'+esc(T('replay_btn'))+'</button>'
    +'</div>';
}

// ═══════════════════════════════════════
// RESPONSE HANDLER
// ═══════════════════════════════════════
function handleResp(d){
  if(d.intent==='scheme') renderScheme(d);
  else if(d.intent==='grievance') renderGrievance(d);
  else renderUnknown(d);
}

function renderScheme(d){
  const resp=d.response||{}; const ln=d.language_name||'English'; const lang=d.language||S.lang;
  let spoken='';
  if(resp.spoken_summary) spoken=resp.spoken_summary;
  else if(resp.schemes&&resp.schemes.length){
    const s=resp.schemes[0];
    spoken=(s.scheme_name?s.scheme_name+' may be relevant to you. ':'')+( s.description||'');
    if(s.benefit) spoken+=' The benefit is: '+s.benefit;
  }
  if(resp.closing_message) spoken+=' '+resp.closing_message;
  let h='<div><span class="lang-tag">'+esc(ln.toUpperCase())+' \u2022 SCHEME INFO</span>';
  h+='<p style="margin-bottom:12px;font-weight:600">'+esc(resp.greeting||'')+'</p>';
  (resp.schemes||[]).forEach(sc=>{
    h+='<div class="result-card"><div class="result-header"><div class="result-icon scheme-icon">&#127963;&#65039;</div><div>'
      +'<div class="result-title">'+esc(sc.scheme_name)+'</div>'
      +'<div class="result-subtitle">Government of India Welfare Scheme</div>'
      +'</div></div>'
      +'<p style="font-size:14px;color:var(--text-secondary);margin-bottom:12px">'+esc(sc.description||'')+'</p>'
      +(sc.benefit?'<div class="benefit-badge">💰 '+esc(sc.benefit)+'</div>':'');
    if(sc.key_eligibility&&sc.key_eligibility.length){
      h+='<p class="section-label">Eligibility</p><ul class="eligibility-list">';
      sc.key_eligibility.forEach(e=>h+='<li>'+esc(e)+'</li>');
      h+='</ul>';
    }
    if(sc.quick_steps&&sc.quick_steps.length){
      h+='<p class="section-label">How to Apply</p><ol class="steps-list">';
      sc.quick_steps.forEach(s=>h+='<li>'+esc(s)+'</li>');
      h+='</ol>';
    }
    if(sc.helpline) h+='<div class="helpline-badge" style="margin-top:10px">📞 '+esc(sc.helpline)+'</div>';
    h+='</div>';
  });
  if(resp.closing_message) h+='<p style="margin-top:14px;font-size:13px;color:var(--text-secondary)">'+esc(resp.closing_message)+'</p>';
  if(spoken) h+=ttsCtrl(spoken.trim(),lang);
  h+='</div>';
  addBot(h);
  if(spoken) setTimeout(()=>speakNow(spoken.trim(),lang),300);
}

function renderGrievance(d){
  const dr=d.draft||{}; const ln=d.language_name||'English'; const lang=d.language||S.lang;
  S.pendingGrievanceId=d.grievance_id;
  const pc=(dr.priority||'medium')==='urgent'?'priority-urgent':(dr.priority||'medium')==='high'?'priority-high':'priority-medium';
  let spoken=(dr.spoken_draft||'');
  if(!spoken&&d.department) spoken='Your complaint has been routed to '+d.department+'.';
  if(dr.confirmation_prompt) spoken+=' '+dr.confirmation_prompt;
  let h='<div><span class="lang-tag">'+esc(ln.toUpperCase())+' \u2022 GRIEVANCE DRAFT</span>'
    +'<p style="margin-bottom:12px;font-weight:600">'+esc(dr.spoken_draft||'Your complaint has been prepared.')+'</p>'
    +'<div class="result-card">'
    +'<div class="result-header"><div class="result-icon grievance-icon">📋</div><div>'
    +'<div class="result-title">'+esc(dr.complaint_title||'Grievance')+'</div>'
    +'<div class="result-subtitle">Grievance ID: '+esc(d.grievance_id)+'</div>'
    +'</div></div>'
    +'<div class="grievance-meta">'
    +'<span class="meta-chip dept-chip">&#127970; '+esc(d.department)+'</span>'
    +'<span class="meta-chip '+pc+'">&#9889; '+(dr.priority||'medium').toUpperCase()+' PRIORITY</span>'
    +'<span class="meta-chip" style="background:rgba(148,163,184,0.1);color:#94a3b8;border:1px solid rgba(148,163,184,0.2)">&#9201;&#65039; '+esc(dr.estimated_resolution||'7 working days (estimate only)')+'</span>'
    +'</div>'
    +'<p class="section-label">Formal Complaint (English)</p>'
    +'<div class="grievance-draft">'+esc(dr.formal_complaint||'')+'</div>';
  if(dr.complaint_tamil) h+='<p class="section-label">Tamil / &#2980;&#2990;&#3007;&#2996;&#3021;</p><div class="grievance-draft" style="font-family:\'Noto Sans Tamil\',sans-serif">'+esc(dr.complaint_tamil)+'</div>';
  if(d.helpline) h+='<div class="helpline-badge" style="margin-top:8px">📞 '+esc(d.helpline)+'</div>';
  h+='</div>'
    +'<p style="margin:14px 0 10px;font-size:14px;color:var(--text-secondary)">'+esc(dr.confirmation_prompt||'Is this complaint correct?')+'</p>'
    +'<div class="confirm-row">'
    +'<button class="btn-confirm btn-yes" onclick="doConfirm(true)">&#9989; Yes, Create Dhvaani Request</button>'
    +'<button class="btn-confirm btn-no" onclick="doConfirm(false)">&#10005; Cancel</button>'
    +'</div>';
  if(spoken.trim()) h+=ttsCtrl(spoken.trim(),lang);
  h+='</div>';
  addBot(h);
  const autoS=(dr.spoken_draft||'').trim();
  if(autoS) setTimeout(()=>speakNow(autoS,lang),300);
}

async function doConfirm(confirmed){
  if(!S.pendingGrievanceId) return;
  stopSpeech();
  document.querySelectorAll('.btn-confirm').forEach(b=>b.disabled=true);
  addUserMsg(confirmed?'✅ Yes, I confirm this complaint.':'✕ Cancel this complaint.');
  addTyping();
  try{
    const r=await fetch('/api/confirm-grievance',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({grievance_id:S.pendingGrievanceId,confirmed})});
    const d=await r.json(); removeTyping(); S.pendingGrievanceId=null;
    if(confirmed&&d.success) renderTracking(d);
    else addBot('<p>Your complaint has been <strong>cancelled</strong>. No problem — you can try again anytime.</p>');
  }catch(e){ removeTyping(); addBot('<p>⚠️ Error processing your request. Please try again.</p>'); }
}

function renderTracking(d){
  const tid=d.tracking_id||'N/A'; const lang=S.lang;
  const spoken='Your Dhvaani request has been created. Tracking ID: '+tid+'.'+(d.department?' Department: '+d.department+'.':'')+' Note: this request has not yet been submitted to the government portal.';
  let h='<div><span class="lang-tag">DHVAANI REQUEST CREATED &#9989;</span>'
    +'<p style="margin-bottom:12px;font-weight:600;color:#4ade80">Your Dhvaani request has been created and is ready for official submission.</p>'
    +'<div class="tracking-card">'
    +'<p style="font-size:12px;color:var(--text-muted);letter-spacing:1px;text-transform:uppercase">Dhvaani Tracking ID</p>'
    +'<p class="tracking-id">'+esc(tid)+'</p>'
    +'<p style="font-size:13px;color:var(--text-secondary);margin-bottom:14px">Save this ID for your records</p>'
    +'<ul class="tracking-steps" style="list-style:none">';
  (d.next_steps||[]).forEach(s=>h+='<li>'+esc(s)+'</li>');
  h+='</ul>';
  if(d.portal) h+='<p style="margin-top:14px;font-size:12px;color:var(--text-muted)">Official portal: <a href="'+d.portal+'" target="_blank" style="color:#93c5fd">'+esc(d.portal)+'</a></p>';
  h+='<p style="margin-top:10px;font-size:11px;color:var(--text-muted);font-style:italic">Note: This Dhvaani request has not yet been submitted to the government portal. Official submission will be supported in a future update.</p>'
    +'</div>'+ttsCtrl(spoken,lang)
    +'<div style="margin-top:16px"><p style="font-size:13px;color:var(--text-secondary);margin-bottom:10px">Need help with anything else?</p>'
    +'<div class="suggestions">'
    +'<button class="suggestion-chip" onclick="useSuggestion(\'Check Ayushman Bharat eligibility\')">Check another scheme</button>'
    +'<button class="suggestion-chip" onclick="useSuggestion(\'The water supply is irregular\')">File another complaint</button>'
    +'</div></div></div>';
  addBot(h);
  showToast('✅ Dhvaani request created! ID: '+tid,'success');
  setTimeout(()=>speakNow('Your Dhvaani request has been created. Tracking ID: '+tid+'.',lang),300);
}

function renderUnknown(d){
  const msg=d.message||'I need a bit more information. Could you try asking differently?';
  let h='<div><span class="lang-tag">DHVAANI</span><p style="margin-bottom:12px">'+esc(msg)+'</p>'
    +'<p style="font-size:13px;color:var(--text-muted);margin-bottom:10px">Try one of these:</p>'
    +'<div class="suggestions">';
  (d.suggestions||[]).forEach(s=>h+='<button class="suggestion-chip" onclick="useSuggestion(\''+s.replace(/'/g,"\\'")+'\')" >'+esc(s)+'</button>');
  h+='</div></div>';
  addBot(h);
  setTimeout(()=>speakNow(msg,S.lang),300);
}

// ═══════════════════════════════════════
// UI HELPERS
// ═══════════════════════════════════════
function addUserTranscript(tx){
  const msgs=document.getElementById('messages');
  const div=document.createElement('div'); div.className='msg user';
  const isTA=/[\u0B80-\u0BFF]/.test(tx); const isHI=/[\u0900-\u097F]/.test(tx);
  const ll=isTA?'TAMIL':isHI?'HINDI':S.lang.toUpperCase();
  div.innerHTML='<div class="msg-avatar">👤</div><div class="msg-bubble">'
    +'<span class="lang-tag">'+ll+' \u2022 VOICE</span>'
    +'<div class="transcript-box"><div class="transcript-label">📝 '+esc(T('you_said'))+'</div>'
    +'<div class="transcript-text">'+esc(tx)+'</div></div></div>';
  msgs.appendChild(div); scrollBot();
}
function addUserMsg(tx){
  const msgs=document.getElementById('messages');
  const div=document.createElement('div'); div.className='msg user';
  div.innerHTML='<div class="msg-avatar">👤</div><div class="msg-bubble"><span class="lang-tag">'+S.lang.toUpperCase()+'</span><p>'+esc(tx)+'</p></div>';
  msgs.appendChild(div); scrollBot();
}
function addBot(html){
  const msgs=document.getElementById('messages');
  const div=document.createElement('div'); div.className='msg dhvaani';
  div.innerHTML='<div class="msg-avatar">&#2343;</div><div class="msg-bubble">'+html+'</div>';
  msgs.appendChild(div); scrollBot();
}
function addTyping(){
  removeTyping();
  const msgs=document.getElementById('messages');
  const div=document.createElement('div'); div.className='msg dhvaani'; div.id='typing-indicator';
  div.innerHTML='<div class="msg-avatar">&#2343;</div><div class="msg-bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
  msgs.appendChild(div); scrollBot();
}
function removeTyping(){ const t=document.getElementById('typing-indicator'); if(t) t.remove(); }
function scrollBot(){ const m=document.getElementById('messages'); m.scrollTop=m.scrollHeight; }
function autoResize(el){ el.style.height='auto'; el.style.height=Math.min(el.scrollHeight,120)+'px'; }
function updateCC(el){ document.getElementById('char-count').textContent=el.value.length+'/600'; }
function showToast(msg,type='info'){
  const t=document.getElementById('toast'); t.textContent=msg; t.className='toast '+type; t.style.display='block';
  setTimeout(()=>t.style.display='none',4000);
}
function esc(s){
  if(!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
}
function toggleDebug(){ S.debugOn=!S.debugOn; document.getElementById('debug-panel').classList.toggle('visible',S.debugOn); }
function dbg(id,v){ const el=document.getElementById(id); if(el) el.textContent=String(v); }

// Alias for backward compat with HTML onclick attributes
const confirmGrievance = doConfirm;
</script>
</body>
</html>
"""

out = os.path.join(os.path.dirname(__file__), 'static', 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(HTML)
print(f"Written {len(HTML)} chars to {out}")
print(f"Size: {os.path.getsize(out)} bytes")
