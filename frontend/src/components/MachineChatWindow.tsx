import { useState, useEffect, useRef } from 'react';
import type { FC, FormEvent } from 'react';
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
}

export const MachineChatWindow: FC<MachineChatWindowProps> = ({
  machineId,
  recentTickets,
  onTicketUpdated,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputSymptom, setInputSymptom] = useState('');
  const [useSimulatedAudio, setUseSimulatedAudio] = useState(false);
  const [useSimulatedImage, setUseSimulatedImage] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resolvedTickets, setResolvedTickets] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with greeting and previous tickets
  useEffect(() => {
    const initial: ChatMessage[] = [
      {
        id: 'init-msg',
        sender: 'bot',
        senderName: 'fixer.ai Advisory Engine',
        text: `Connected to ${machineId} isolated diagnostic context (Tier 1 manual + Tier 2 historical repairs). Describe observed symptoms, attach photos, or record voice notes to begin multimodal fault diagnosis.`,
        timestamp: new Date().toISOString(),
      },
    ];
    setMessages(initial);
  }, [machineId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!inputSymptom && !useSimulatedAudio && !useSimulatedImage) return;

    const userText = inputSymptom || (useSimulatedAudio ? 'Simulated technician voice report' : 'Inspection inquiry');
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'technician',
      senderName: 'Technician',
      text: userText,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputSymptom('');
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('symptom_text', userText);

      if (useSimulatedAudio) {
        // Simulated audio bytes
        const blob = new Blob(['RIFF....WAVEfmt ....data....'], { type: 'audio/wav' });
        formData.append('audio_file', blob, 'audio_inspection.wav');
      }

      if (useSimulatedImage) {
        // Simulated image bytes
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
        text: `Diagnosis generated for ${machineId}. Status: ${data.decision?.action === 'escalate' ? 'ESCALATED TO SLACK' : 'SELF-RESOLVE'}`,
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
      setUseSimulatedAudio(false);
      setUseSimulatedImage(false);
    }
  };

  const handleMarkResolved = async (ticketId: string) => {
    try {
      await axios.post(`/api/tickets/${ticketId}/resolve`, {
        resolution_summary: `Resolved by technician in web UI. Inspection and verification steps completed.`,
        technician_notes: `Repair verified under production load. Nominal vibration/temperature restored.`,
      });

      setResolvedTickets((prev) => ({ ...prev, [ticketId]: true }));
      onTicketUpdated();

      // Add confirmation bot message
      setMessages((prev) => [
        ...prev,
        {
          id: `resolved-${Date.now()}`,
          sender: 'bot',
          senderName: 'fixer.ai Continual Learning',
          text: `✅ Ticket ${ticketId.slice(0, 8)} marked RESOLVED. Full incident log and technician resolution embedded into ${machineId} Tier 2 collection. The machine will now recall this fix for future incidents.`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      console.error('Failed to resolve ticket:', err);
    }
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '620px', overflow: 'hidden' }}>
      {/* Chat Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        background: 'rgba(0, 0, 0, 0.25)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.85rem',
          }}>
            🤖
          </div>
          <div>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
              Multimodal Advisory Assistant
            </h3>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              Scoped to {machineId} • Isolated Tier 2 Memory
            </span>
          </div>
        </div>

        <span style={{
          fontSize: '0.7rem',
          color: '#34d399',
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          padding: '3px 9px',
          borderRadius: '12px',
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
                maxWidth: isUser ? '75%' : '88%',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}
            >
              <div style={{
                fontSize: '0.72rem',
                color: '#64748b',
                alignSelf: isUser ? 'flex-end' : 'flex-start',
                display: 'flex',
                gap: '8px',
              }}>
                <span style={{ fontWeight: 600, color: isUser ? '#38bdf8' : '#a78bfa' }}>{m.senderName}</span>
                <span>{new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              </div>

              <div style={{
                background: isUser ? 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)' : 'rgba(15, 23, 42, 0.9)',
                border: `1px solid ${isUser ? 'rgba(59, 130, 246, 0.4)' : 'rgba(255, 255, 255, 0.08)'}`,
                borderRadius: '14px',
                padding: '14px 18px',
                color: '#f8fafc',
                fontSize: '0.86rem',
                lineHeight: 1.5,
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.25)',
              }}>
                {m.text}

                {/* Structured Diagnosis Card if available */}
                {m.diagnosis && (
                  <div style={{
                    marginTop: '14px',
                    padding: '14px',
                    borderRadius: '12px',
                    background: 'rgba(0, 0, 0, 0.35)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                  }}>
                    {/* Severity & Confidence */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <span style={{
                        textTransform: 'uppercase',
                        fontWeight: 700,
                        fontSize: '0.74rem',
                        padding: '2px 8px',
                        borderRadius: '6px',
                        background: m.diagnosis.severity === 'critical' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: m.diagnosis.severity === 'critical' ? '#f87171' : '#fbbf24',
                        border: `1px solid ${m.diagnosis.severity === 'critical' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                      }}>
                        Severity: {m.diagnosis.severity}
                      </span>
                      <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                        Confidence: <strong style={{ color: '#38bdf8' }}>{Math.round((m.diagnosis.confidence || 0.8) * 100)}%</strong>
                      </span>
                    </div>

                    {/* Top Diagnosis */}
                    {m.diagnosis.ranked_diagnoses && m.diagnosis.ranked_diagnoses[0] && (
                      <div style={{ marginBottom: '10px' }}>
                        <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.88rem' }}>
                          {m.diagnosis.ranked_diagnoses[0].diagnosis}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: '#94a3b8', fontStyle: 'italic', marginTop: '2px' }}>
                          Evidence: {m.diagnosis.ranked_diagnoses[0].evidence}
                        </div>
                      </div>
                    )}

                    {/* Repair Steps */}
                    {m.diagnosis.repair_steps && (
                      <div style={{ marginTop: '10px' }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#a5b4fc', textTransform: 'uppercase', marginBottom: '4px' }}>
                          Synthesized Repair Checklist (OEM Manual):
                        </div>
                        <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '0.78rem', color: '#cbd5e1' }}>
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
                        borderRadius: '8px',
                        background: 'rgba(99, 102, 241, 0.1)',
                        border: '1px solid rgba(99, 102, 241, 0.25)',
                        fontSize: '0.78rem',
                        color: '#c7d2fe',
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
                          <span style={{ fontSize: '0.78rem', color: '#34d399', fontWeight: 600 }}>
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
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(7, 10, 19, 0.9)',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
        }}
      >
        {/* Multimodal Attachment Toggles */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.75rem' }}>
          <button
            type="button"
            onClick={() => setUseSimulatedAudio((v) => !v)}
            style={{
              background: useSimulatedAudio ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.05)',
              border: `1px solid ${useSimulatedAudio ? '#10b981' : 'rgba(255, 255, 255, 0.1)'}`,
              color: useSimulatedAudio ? '#34d399' : '#94a3b8',
              padding: '4px 10px',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>🎙️</span>
            <span>{useSimulatedAudio ? 'Voice Note Attached' : '+ Add Voice Note'}</span>
          </button>

          <button
            type="button"
            onClick={() => setUseSimulatedImage((v) => !v)}
            style={{
              background: useSimulatedImage ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255, 255, 255, 0.05)',
              border: `1px solid ${useSimulatedImage ? '#06b6d4' : 'rgba(255, 255, 255, 0.1)'}`,
              color: useSimulatedImage ? '#38bdf8' : '#94a3b8',
              padding: '4px 10px',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>📷</span>
            <span>{useSimulatedImage ? 'Inspection Photo Attached' : '+ Add Photo'}</span>
          </button>
        </div>

        {/* Text Input Row */}
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            id="input-symptom"
            type="text"
            value={inputSymptom}
            onChange={(e) => setInputSymptom(e.target.value)}
            placeholder="Type symptom observation (e.g. grinding noise on J2 axis, getting warm)..."
            style={{
              flex: 1,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '10px',
              padding: '10px 14px',
              color: '#f8fafc',
              fontSize: '0.85rem',
              outline: 'none',
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
