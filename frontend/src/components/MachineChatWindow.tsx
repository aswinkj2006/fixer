import { useState, useEffect, useRef } from 'react';
import type { FC, FormEvent, ChangeEvent } from 'react';
import axios from 'axios';
import type { TicketSummary } from '../types';

interface MachineChatWindowProps {
  machineId: string;
  recentTickets: TicketSummary[];
  onTicketUpdated: () => void;
}

interface ChatMessage {
  id: string;
  sender: 'bot' | 'technician';
  senderName?: string;
  text: string;
  timestamp: string;
  diagnosis?: any;
  decision?: any;
  ticketId?: string;
  hasAudio?: boolean;
  hasImage?: boolean;
  imagePreviewUrl?: string;
}

const DEFECT_PRESETS = [
  {
    id: 'm01',
    machineId: 'M-01',
    title: 'J2 Gearbox Grease Leak',
    img: '/defects/m01_gearbox_leak.jpg',
    suggestedText: 'Dark grease leaking past J2 gearbox seal with metal flakes; motor temperature rising.',
  },
  {
    id: 'm02',
    machineId: 'M-02',
    title: 'Spindle Chatter & Runout',
    img: '/defects/m02_spindle_chatter.jpg',
    suggestedText: 'Severe radial chatter on milled workpiece; high-pitch whine at 8000 RPM.',
  },
  {
    id: 'm03',
    machineId: 'M-03',
    title: 'Motor Drive-End Overheat',
    img: '/defects/m03_motor_overheat.jpg',
    suggestedText: 'Conveyor drive motor running extremely hot; grease degradation on bearing cover.',
  },
];

export const MachineChatWindow: FC<MachineChatWindowProps> = ({
  machineId,
  recentTickets,
  onTicketUpdated,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputSymptom, setInputSymptom] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resolvedTickets, setResolvedTickets] = useState<Record<string, boolean>>({});

  // Real Audio Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [recordedAudioBlob, setRecordedAudioBlob] = useState<Blob | null>(null);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(null);
  const [useSimulatedAudio, setUseSimulatedAudio] = useState(false);

  // Real / Preset Image State
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [selectedImageUrl, setSelectedImageUrl] = useState<string | null>(null);
  const [selectedImageName, setSelectedImageName] = useState<string | null>(null);
  const [useSimulatedImage, setUseSimulatedImage] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize with greeting
  useEffect(() => {
    const initial: ChatMessage[] = [
      {
        id: 'init-msg',
        sender: 'bot',
        senderName: 'fixer.ai Advisory Engine',
        text: `Connected to ${machineId} isolated diagnostic context (Tier 1 manual + Tier 2 historical repairs). Describe observed symptoms, attach inspection photos, or record voice notes to begin multimodal fault diagnosis.`,
        timestamp: new Date().toISOString(),
      },
    ];
    setMessages(initial);
  }, [machineId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Audio Recording Controls
  const startRecording = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setUseSimulatedAudio(true);
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setRecordedAudioBlob(blob);
        setRecordedAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      setIsRecording(true);
      setRecordingDuration(0);
      recordingTimerRef.current = window.setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.warn('Microphone access unavailable or denied:', err);
      setUseSimulatedAudio(true);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }
  };

  const clearAudio = () => {
    setRecordedAudioBlob(null);
    if (recordedAudioUrl) {
      URL.revokeObjectURL(recordedAudioUrl);
      setRecordedAudioUrl(null);
    }
    setRecordingDuration(0);
    setUseSimulatedAudio(false);
  };

  // Image Handling
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImageFile(file);
      setSelectedImageUrl(URL.createObjectURL(file));
      setSelectedImageName(file.name);
      setUseSimulatedImage(false);
    }
  };

  const selectPreset = async (preset: typeof DEFECT_PRESETS[0]) => {
    try {
      const response = await fetch(preset.img);
      const blob = await response.blob();
      const file = new File([blob], `${preset.id}_defect.jpg`, { type: 'image/jpeg' });
      setSelectedImageFile(file);
      setSelectedImageUrl(preset.img);
      setSelectedImageName(preset.title);
      setUseSimulatedImage(false);
      if (!inputSymptom) {
        setInputSymptom(preset.suggestedText);
      }
    } catch (e) {
      console.warn('Could not load preset image:', e);
      setUseSimulatedImage(true);
    }
  };

  const clearImage = () => {
    setSelectedImageFile(null);
    if (selectedImageUrl && selectedImageUrl.startsWith('blob:')) {
      URL.revokeObjectURL(selectedImageUrl);
    }
    setSelectedImageUrl(null);
    setSelectedImageName(null);
    setUseSimulatedImage(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    const hasAudio = Boolean(recordedAudioBlob || useSimulatedAudio);
    const hasImage = Boolean(selectedImageFile || useSimulatedImage);

    if (!inputSymptom && !hasAudio && !hasImage) return;

    const userText = inputSymptom || (hasAudio ? 'Technician live voice report' : 'Defect photo inspection');
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'technician',
      senderName: 'Technician',
      text: userText,
      timestamp: new Date().toISOString(),
      hasAudio,
      hasImage,
      imagePreviewUrl: selectedImageUrl || undefined,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputSymptom('');
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('symptom_text', userText);

      // Attach Audio
      if (recordedAudioBlob) {
        formData.append('audio_file', recordedAudioBlob, 'voice_report.webm');
      } else if (useSimulatedAudio) {
        const blob = new Blob(['RIFF....WAVEfmt ....data....'], { type: 'audio/wav' });
        formData.append('audio_file', blob, 'audio_inspection.wav');
      }

      // Attach Image
      if (selectedImageFile) {
        formData.append('image_file', selectedImageFile, selectedImageFile.name || 'defect_inspection.jpg');
      } else if (useSimulatedImage) {
        const blob = new Blob(['\xFF\xD8\xFF\xE0\x00\x10JFIF'], { type: 'image/jpeg' });
        formData.append('image_file', blob, 'defect_inspection.jpg');
      }

      const res = await axios.post(`/api/chat/${machineId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const data = res.data;
      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: 'bot',
        senderName: 'fixer.ai',
        text: `Diagnosis generated for ${machineId}. Action: ${data.decision?.action === 'escalate' ? 'ESCALATED TO SLACK' : 'SELF-RESOLVE'}`,
        timestamp: new Date().toISOString(),
        diagnosis: data.diagnosis,
        decision: data.decision,
        ticketId: data.ticket_id,
      };

      setMessages((prev) => [...prev, botMsg]);
      onTicketUpdated();
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `bot-err-${Date.now()}`,
        sender: 'bot',
        senderName: 'fixer.ai',
        text: `Diagnostic evaluation encountered an error: ${err.message}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSubmitting(false);
      clearAudio();
      clearImage();
    }
  };

  const handleMarkResolved = async (ticketId: string) => {
    try {
      await axios.post(`/api/tickets/${ticketId}/resolve`, {
        resolution_summary: `Resolved by technician in web UI. Verification steps completed.`,
        technician_notes: `Repair verified under production load. Nominal vibration/temperature restored.`,
      });

      setResolvedTickets((prev) => ({ ...prev, [ticketId]: true }));
      onTicketUpdated();

      setMessages((prev) => [
        ...prev,
        {
          id: `resolved-${Date.now()}`,
          sender: 'bot',
          senderName: 'fixer.ai Continual Learning',
          text: `✅ Ticket ${ticketId.slice(0, 8)} marked RESOLVED. Incident log and technician resolution embedded into ${machineId} Tier 2 collection. The machine will recall this fix for future occurrences.`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      console.error('Failed to resolve ticket:', err);
    }
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '640px', overflow: 'hidden' }}>
      {/* Chat Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-card)',
        background: 'var(--bg-card-subtle)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: 'var(--btn-radius)',
            background: 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.85rem',
            color: '#ffffff',
          }}>
            🤖
          </div>
          <div>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Multimodal Advisory Assistant
            </h3>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Scoped to {machineId} • Isolated Tier 2 Memory
            </span>
          </div>
        </div>

        <span style={{
          fontSize: '0.7rem',
          color: 'var(--status-healthy)',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          padding: '3px 9px',
          borderRadius: 'var(--btn-radius)',
          fontWeight: 600,
        }}>
          ● Tier 1/2 Active ({recentTickets.length} past records)
        </span>
      </div>

      {/* Messages Timeline */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}>
        {messages.map((m) => {
          const isUser = m.sender === 'technician';

          return (
            <div
              key={m.id}
              style={{
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                maxWidth: isUser ? '80%' : '90%',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}
            >
              <div style={{
                fontSize: '0.72rem',
                color: 'var(--text-muted)',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                display: 'flex',
                gap: '8px',
              }}>
                <span style={{ fontWeight: 600, color: isUser ? 'var(--accent-blue)' : 'var(--accent-violet)' }}>{m.senderName}</span>
                <span>{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>

              <div style={{
                background: isUser ? 'linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)' : 'var(--chat-bubble-bot)',
                border: `1px solid ${isUser ? 'rgba(37, 99, 235, 0.4)' : 'var(--chat-bubble-bot-border)'}`,
                borderRadius: 'var(--btn-radius)',
                padding: '14px 18px',
                color: isUser ? '#ffffff' : 'var(--text-primary)',
                fontSize: '0.86rem',
                lineHeight: 1.5,
                boxShadow: '0 2px 10px rgba(0, 0, 0, 0.08)',
              }}>
                {/* Media Attachment Badges in Message */}
                {(m.hasAudio || m.hasImage) && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
                    {m.hasAudio && (
                      <span style={{
                        fontSize: '0.7rem',
                        background: 'rgba(16, 185, 129, 0.15)',
                        color: 'var(--status-healthy)',
                        padding: '2px 8px',
                        borderRadius: 'var(--btn-radius)',
                        fontWeight: 600,
                      }}>
                        🎙️ Voice Note Included
                      </span>
                    )}
                    {m.hasImage && (
                      <span style={{
                        fontSize: '0.7rem',
                        background: 'rgba(37, 99, 235, 0.15)',
                        color: 'var(--accent-blue)',
                        padding: '2px 8px',
                        borderRadius: 'var(--btn-radius)',
                        fontWeight: 600,
                      }}>
                        📷 Defect Photo Attached
                      </span>
                    )}
                  </div>
                )}

                {/* Optional Image Preview inside Message */}
                {m.imagePreviewUrl && (
                  <div style={{ marginBottom: '10px', borderRadius: 'var(--btn-radius)', overflow: 'hidden', maxWidth: '240px', border: '1px solid var(--border-card)' }}>
                    <img src={m.imagePreviewUrl} alt="Defect" style={{ width: '100%', height: 'auto', display: 'block' }} />
                  </div>
                )}

                {m.text}

                {/* Structured Diagnosis Card if available */}
                {m.diagnosis && (
                  <div style={{
                    marginTop: '14px',
                    padding: '14px',
                    borderRadius: 'var(--btn-radius)',
                    background: 'var(--bg-card-subtle)',
                    border: '1px solid var(--border-card)',
                  }}>
                    {/* Severity & Confidence */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{
                        textTransform: 'uppercase',
                        fontWeight: 700,
                        fontSize: '0.74rem',
                        padding: '2px 8px',
                        borderRadius: 'var(--btn-radius)',
                        background: m.diagnosis.severity === 'critical' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: m.diagnosis.severity === 'critical' ? 'var(--status-critical)' : 'var(--status-warning)',
                        border: `1px solid ${m.diagnosis.severity === 'critical' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                      }}>
                        Severity: {m.diagnosis.severity}
                      </span>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        Confidence: <strong style={{ color: 'var(--accent-blue)' }}>{Math.round((m.diagnosis.confidence || 0.8) * 100)}%</strong>
                      </span>
                    </div>

                    {/* Top Diagnosis */}
                    {m.diagnosis.ranked_diagnoses && m.diagnosis.ranked_diagnoses[0] && (
                      <div style={{ marginBottom: '10px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.88rem' }}>
                          {m.diagnosis.ranked_diagnoses[0].diagnosis}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: '2px' }}>
                          Evidence: {m.diagnosis.ranked_diagnoses[0].evidence}
                        </div>
                      </div>
                    )}

                    {/* Repair Steps */}
                    {m.diagnosis.repair_steps && (
                      <div style={{ marginTop: '10px' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-blue)', textTransform: 'uppercase', marginBottom: '4px' }}>
                          Synthesized Repair Checklist (OEM Manual):
                        </div>
                        <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                          {m.diagnosis.repair_steps.map((step: string, idx: number) => (
                            <li key={idx} style={{ marginBottom: '3px' }}>{step}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Slack Escalation Status */}
                    {m.decision && m.decision.action === 'escalate' && (
                      <div style={{
                        marginTop: '12px',
                        padding: '8px 12px',
                        borderRadius: 'var(--btn-radius)',
                        background: 'rgba(37, 99, 235, 0.1)',
                        border: '1px solid rgba(37, 99, 235, 0.25)',
                        fontSize: '0.78rem',
                        color: 'var(--accent-blue)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}>
                        <span>📢 Escalated to <strong>#fixer-ai-escalations</strong></span>
                        <span>Assigned: <strong>{m.decision.assigned_technician?.name || 'Technician'}</strong></span>
                      </div>
                    )}

                    {/* Mark Resolved Action */}
                    {m.ticketId && (
                      <div style={{ marginTop: '14px', display: 'flex', justifyContent: 'flex-end' }}>
                        {resolvedTickets[m.ticketId] ? (
                          <span style={{ fontSize: '0.78rem', color: 'var(--status-healthy)', fontWeight: 600 }}>
                            ✓ Resolved & Embedded into Tier 2
                          </span>
                        ) : (
                          <button
                            className="btn-primary"
                            style={{ padding: '6px 14px', fontSize: '0.78rem' }}
                            onClick={() => m.ticketId && handleMarkResolved(m.ticketId)}
                          >
                            Mark Resolved (Test Continual Learning)
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Multimodal Input Controls */}
      <form
        onSubmit={handleSend}
        style={{
          padding: '16px 20px',
          borderTop: '1px solid var(--border-card)',
          background: 'var(--bg-card-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}
      >
        {/* Active Attachment Previews (Audio & Image) */}
        {(recordedAudioBlob || useSimulatedAudio || selectedImageUrl || useSimulatedImage) && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '8px 12px',
            borderRadius: 'var(--btn-radius)',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-card)',
            fontSize: '0.75rem',
            flexWrap: 'wrap',
          }}>
            {/* Audio Attachment Preview */}
            {(recordedAudioBlob || useSimulatedAudio) && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--status-healthy)' }}>
                <span>🎵</span>
                <span>{recordedAudioBlob ? `Voice Note (${recordingDuration || '1'}s)` : 'Simulated Voice Note'}</span>
                {recordedAudioUrl && (
                  <audio src={recordedAudioUrl} controls style={{ height: '24px', maxWidth: '160px' }} />
                )}
                <button
                  type="button"
                  onClick={clearAudio}
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '0 4px' }}
                >
                  ✕
                </button>
              </div>
            )}

            {/* Image Attachment Preview */}
            {(selectedImageUrl || useSimulatedImage) && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-blue)' }}>
                {selectedImageUrl ? (
                  <img
                    src={selectedImageUrl}
                    alt="Preview"
                    style={{ width: '24px', height: '24px', objectFit: 'cover', borderRadius: '4px' }}
                  />
                ) : (
                  <span>📷</span>
                )}
                <span>{selectedImageName || (useSimulatedImage ? 'Simulated Defect Photo' : 'Photo Attached')}</span>
                <button
                  type="button"
                  onClick={clearImage}
                  style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '0 4px' }}
                >
                  ✕
                </button>
              </div>
            )}
          </div>
        )}

        {/* Multimodal Action Bar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px', fontSize: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {/* Real Microphone Recording Button */}
            {isRecording ? (
              <button
                type="button"
                onClick={stopRecording}
                style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid var(--status-critical)',
                  color: 'var(--status-critical)',
                  padding: '6px 12px',
                  borderRadius: 'var(--btn-radius)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontWeight: 700,
                  animation: 'pulse 1.5s infinite',
                }}
              >
                <span>⏹️</span>
                <span>Stop ({recordingDuration}s)</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={startRecording}
                className="btn-secondary"
                style={{ padding: '6px 12px', fontSize: '0.78rem' }}
              >
                <span>🎙️</span>
                <span>Record Voice</span>
              </button>
            )}

            {/* Native File Upload */}
            <input
              type="file"
              accept="image/*"
              ref={fileInputRef}
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.78rem' }}
            >
              <span>📷</span>
              <span>Upload Photo</span>
            </button>
          </div>

          {/* Quick-Select Defect Samples */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Defect Samples:</span>
            {DEFECT_PRESETS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => selectPreset(p)}
                style={{
                  background: selectedImageName === p.title ? 'rgba(37, 99, 235, 0.18)' : 'var(--bg-card-subtle)',
                  border: selectedImageName === p.title ? '1px solid var(--accent-blue)' : '1px solid var(--border-card)',
                  color: selectedImageName === p.title ? 'var(--accent-blue)' : 'var(--text-muted)',
                  padding: '3px 8px',
                  borderRadius: 'var(--btn-radius)',
                  cursor: 'pointer',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  transition: 'all 0.15s ease',
                }}
              >
                {p.machineId} Defect
              </button>
            ))}
          </div>
        </div>

        {/* Text Input Row */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            id="input-symptom"
            type="text"
            value={inputSymptom}
            onChange={(e) => setInputSymptom(e.target.value)}
            placeholder="Type observed symptoms, attach photo, or click Record Voice..."
            style={{
              flex: 1,
              background: 'var(--input-bg)',
              border: '1px solid var(--input-border)',
              borderRadius: 'var(--btn-radius)',
              padding: '10px 14px',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              outline: 'none',
              boxShadow: 'inset 0 1px 2px rgba(0, 0, 0, 0.05)',
            }}
          />

          <button
            id="btn-send-chat"
            type="submit"
            className="btn-primary"
            disabled={isSubmitting}
            style={{ padding: '10px 20px' }}
          >
            {isSubmitting ? 'Diagnosing...' : 'Send'}
          </button>
        </div>
      </form>
    </div>
  );
};
