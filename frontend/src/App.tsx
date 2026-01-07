import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import {
  Shield,
  Inbox,
  PieChart,
  Settings,
  Users,
  Bell,
  Menu,
  Sun,
  Moon,
  Database,
  Gavel,
  AlertTriangle,
  UserCheck,
  Play,
  Check,
  Loader2,
  Download,
  Search,
  Activity,
  CheckCircle,
  Eye,
  EyeOff,
  FileJson,
  Cpu,
  Key,
  Save,
  Plus,
  Trash2,
  MoreHorizontal,
} from 'lucide-react';

// --- Configuration ---
const COLORS = {
  paypal: {
    blue: '#003087',
    lightblue: '#009cde',
    darkblue: '#001a6d',
    yellow: '#ffc439',
    gray: '#e6e6e6',
  },
  fraud: {
    high: '#d92d20',
    medium: '#fdb022',
    low: '#12b76a',
  },
};

const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8000';

// --- Types ---
type Theme = 'light' | 'dark';
type AgentStatus = 'idle' | 'running' | 'completed';
type View = 'queue' | 'analytics' | 'rules' | 'team' | 'settings';

type CasePacket = {
  found: boolean;
  trans_id: string;
  transaction?: {
    trans_id: string;
    user_id: string;
    amount: number;
    merchant: string;
    device_ip: string;
    shipping_addr: string;
    billing_addr: string;
    timestamp: string;
    name?: string | null;
    email?: string | null;
    home_ip?: string | null;
    account_age_days?: number;
    vip_status?: string;
    country?: string;
  };
  user_history?: any;
  ip_intel?: any;
  kyc?: any;
  disputes?: any;
  similar_cases?: any;
};

type DecisionPacket = {
  transaction_id: string;
  model_version: string;
  risk_score: number;
  decision: 'ALLOW' | 'CHALLENGE' | 'DENY';
  reason_codes: string[];
  rule_hits: string[];
  decision_event_id?: string;
};

type InvestigatePacket = DecisionPacket & {
  artifacts_dir?: string;
  agent_outputs?: any;
};

type Kpis = {
  window_days: number;
  total_events: number;
  decline_rate: number;
  challenge_rate: number;
  allow_rate: number;
  total_volume: number;
  chargeback_amount: number;
  loss_rate_proxy: number;
};

function getStoredApiKey(): string {
  try {
    return localStorage.getItem('fraudshield_api_key') || '';
  } catch {
    return '';
  }
}

function setStoredApiKey(key: string) {
  try {
    localStorage.setItem('fraudshield_api_key', key);
  } catch {
    // ignore
  }
}

function apiClient(apiKey: string) {
  const headers: Record<string, string> = {};
  if (apiKey) headers['X-API-Key'] = apiKey;
  return axios.create({ baseURL: API_BASE, headers });
}

// --- Main Component ---
export default function App() {
  const [theme, setTheme] = useState<Theme>('light');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [activeView, setActiveView] = useState<View>('queue');

  // Transaction selection
  const [transId, setTransId] = useState<string>('TX-999');
  const [casePacket, setCasePacket] = useState<CasePacket | null>(null);
  const [caseLoading, setCaseLoading] = useState(false);
  const [caseError, setCaseError] = useState<string | null>(null);

  // Decision / investigation
  const [decisionPacket, setDecisionPacket] = useState<DecisionPacket | null>(null);
  const [investigationPacket, setInvestigationPacket] = useState<InvestigatePacket | null>(null);
  const [showPII, setShowPII] = useState(false);
  const [investigationState, setInvestigationState] = useState<AgentStatus>('idle');

  // API key (frontend-side, optional)
  const [apiKey, setApiKey] = useState<string>(getStoredApiKey());

  const client = useMemo(() => apiClient(apiKey), [apiKey]);

  // Analytics
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [kpisLoading, setKpisLoading] = useState(false);

  const agents = useMemo(
    () => [
      { name: 'Data Collector', role: 'Ops Copilot', status: 'completed', duration: '2.4s', icon: <Database size={16} /> },
      { name: 'Pattern Detector', role: 'Threat Intel', status: investigationState === 'running' ? 'running' : investigationState === 'completed' ? 'completed' : 'idle', duration: investigationState === 'completed' ? '1.2s' : '', icon: <Shield size={16} /> },
      { name: 'Policy Engine', role: 'Governance', status: investigationState === 'completed' ? 'completed' : investigationState === 'running' ? 'running' : 'idle', duration: investigationState === 'completed' ? '0.8s' : '', icon: <Gavel size={16} /> },
    ] as Array<{ name: string; role: string; status: AgentStatus; duration: string; icon: React.ReactNode }>,
    [investigationState],
  );

  const isDark = theme === 'dark';

  // Toggle Theme
  const toggleTheme = () => setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));

  // PII Masking Helper
  const mask = (text: string, type: 'email' | 'text' = 'text') => {
    if (showPII) return text;
    if (!text) return '';
    if (type === 'email') {
      const parts = text.split('@');
      if (parts.length !== 2) return '***';
      const [name, domain] = parts;
      return `${name.substring(0, 1)}***@${domain}`;
    }
    return `${text.substring(0, 1)}••••`;
  };

  const fetchCase = async () => {
    setCaseLoading(true);
    setCaseError(null);
    try {
      const res = await client.get<CasePacket>(`/case/${encodeURIComponent(transId)}`);
      setCasePacket(res.data);
      setDecisionPacket(null);
      setInvestigationPacket(null);
      setInvestigationState('idle');
    } catch (e: any) {
      setCasePacket(null);
      setCaseError(e?.response?.data?.detail || 'Unable to fetch case. Ensure the API is running.');
    } finally {
      setCaseLoading(false);
    }
  };

  const runDecision = async () => {
    setCaseError(null);
    try {
      const res = await client.post<DecisionPacket>('/decision', { trans_id: transId });
      setDecisionPacket(res.data);
      setInvestigationPacket(null);
    } catch (e: any) {
      setCaseError(e?.response?.data?.detail || 'Decision failed.');
    }
  };

  // Run investigation (server-side agents if enabled)
  const runAnalysis = async () => {
    setInvestigationState('running');
    setCaseError(null);
    try {
      const res = await client.post<InvestigatePacket>('/investigate', { trans_id: transId });
      setInvestigationPacket(res.data);
      setDecisionPacket(res.data);
      setInvestigationState('completed');
    } catch (e: any) {
      setInvestigationState('idle');
      setCaseError(e?.response?.data?.detail || 'Investigation failed.');
    }
  };

  const refreshKpis = async (windowDays: number) => {
    setKpisLoading(true);
    try {
      const res = await client.get<Kpis>(`/kpis?window_days=${windowDays}`);
      setKpis(res.data);
    } catch (e: any) {
      setCaseError(e?.response?.data?.detail || 'Failed to load KPIs.');
    } finally {
      setKpisLoading(false);
    }
  };

  useEffect(() => {
    // initial load
    fetchCase();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const t = casePacket?.transaction;
  const effectiveDecision = investigationPacket || decisionPacket;

  return (
    <div
      className={`min-h-screen font-sans transition-colors duration-300 ${
        isDark ? 'bg-gray-900 text-gray-200' : 'bg-[#e6e6e6] text-gray-800'
      }`}
    >
      {/* Theme Toggle (Fixed) */}
      <div className="fixed bottom-4 right-4 z-50">
        <button
          onClick={toggleTheme}
          className="p-3 rounded-full text-white shadow-lg transition-colors hover:opacity-90"
          style={{ backgroundColor: COLORS.paypal.blue }}
        >
          {isDark ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </div>

      <div className="flex h-screen overflow-hidden">
        {/* SIDEBAR (PayPal Blue) */}
        <div className={`hidden md:flex md:flex-shrink-0 transition-all duration-300 ${isSidebarOpen ? 'w-64' : 'w-20'}`}>
          <div className="flex flex-col w-full text-white h-full" style={{ backgroundColor: COLORS.paypal.blue }}>
            {/* Logo Area */}
            <div className="flex items-center h-16 px-4 shrink-0" style={{ backgroundColor: COLORS.paypal.darkblue }}>
              <div className="flex items-center justify-center w-full md:justify-start">
                <Shield className="h-8 w-8 text-white fill-current opacity-90" />
                {isSidebarOpen && <h1 className="text-xl font-bold ml-2 tracking-tight">FraudShield</h1>}
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
              <NavItem icon={<Inbox size={20} />} label="Case Queue" active={activeView === 'queue'} isOpen={isSidebarOpen} onClick={() => setActiveView('queue')} />
              <NavItem icon={<PieChart size={20} />} label="Risk Analytics" active={activeView === 'analytics'} isOpen={isSidebarOpen} onClick={() => setActiveView('analytics')} />
              <NavItem icon={<Gavel size={20} />} label="Rules Engine" active={activeView === 'rules'} isOpen={isSidebarOpen} onClick={() => setActiveView('rules')} />
              <NavItem icon={<Users size={20} />} label="Team Settings" active={activeView === 'team'} isOpen={isSidebarOpen} onClick={() => setActiveView('team')} />
            </nav>

            {/* LLM Settings Button (Bottom) */}
            <div className="px-2 pb-2">
              <NavItem
                icon={<Key size={20} />}
                label="LLM Config"
                active={activeView === 'settings'}
                isOpen={isSidebarOpen}
                onClick={() => setActiveView('settings')}
                className="bg-[#001a6d]/50 hover:bg-[#001a6d] mt-2"
              />
            </div>

            {/* User Profile */}
            <div className="p-4 border-t border-[#009cde]/30 shrink-0">
              <div className="flex items-center">
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center font-bold text-xs shrink-0">RA</div>
                {isSidebarOpen && (
                  <div className="ml-3 truncate">
                    <p className="text-sm font-medium">Risk Admin</p>
                    <p className="text-xs text-blue-200">Risk Operations</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* MAIN CONTENT */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Header */}
          <header
            className={`flex items-center justify-between h-16 px-6 border-b shrink-0 transition-colors ${
              isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
            }`}
          >
            <div className="flex items-center gap-3">
              <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="md:hidden p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700">
                <Menu size={20} />
              </button>

              {/* Search transaction */}
              <div className="flex items-center gap-2">
                <div className={`flex items-center gap-2 px-3 py-2 rounded border ${isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-200'}`}>
                  <Search size={16} className={isDark ? 'text-gray-300' : 'text-gray-500'} />
                  <input
                    value={transId}
                    onChange={(e) => setTransId(e.target.value)}
                    className={`bg-transparent outline-none text-sm w-40 ${isDark ? 'text-gray-100' : 'text-gray-800'}`}
                    placeholder="Transaction ID"
                  />
                </div>
                <button
                  onClick={fetchCase}
                  disabled={caseLoading}
                  className="px-3 py-2 rounded text-sm font-medium text-white hover:opacity-90 disabled:opacity-70"
                  style={{ backgroundColor: COLORS.paypal.blue }}
                >
                  {caseLoading ? 'Loading…' : 'Load'}
                </button>
                <button
                  onClick={runDecision}
                  className={`px-3 py-2 rounded text-sm font-medium border ${isDark ? 'border-gray-600 hover:bg-gray-700' : 'border-gray-200 hover:bg-gray-50'}`}
                >
                  Run Decision
                </button>
              </div>

              {/* Dynamic Header Title */}
              <div className="ml-2">
                {activeView === 'queue' && (
                  <h2 className="text-lg font-medium flex items-center gap-2">
                    Case #{transId}
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500">
                      {investigationState === 'running' ? 'ANALYZING…' : casePacket?.found ? 'OPEN' : 'NOT FOUND'}
                    </span>
                  </h2>
                )}
                {activeView === 'analytics' && <h2 className="text-lg font-medium">Risk Performance Dashboard</h2>}
                {activeView === 'rules' && <h2 className="text-lg font-medium">Decision Rules Engine</h2>}
                {activeView === 'team' && <h2 className="text-lg font-medium">Team Management</h2>}
                {activeView === 'settings' && <h2 className="text-lg font-medium">System Configuration</h2>}
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="relative cursor-pointer">
                <Bell size={20} className="text-gray-500 dark:text-gray-300" />
                <span
                  className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border-2 border-white dark:border-gray-800"
                  style={{ backgroundColor: COLORS.fraud.high }}
                ></span>
              </div>
              <div className="flex items-center bg-red-50 dark:bg-red-900/20 px-3 py-1 rounded-full border border-red-100 dark:border-red-900/30">
                <span className="text-sm font-medium mr-2 text-gray-600 dark:text-gray-300">Risk Level:</span>
                <span className="text-xs font-bold" style={{ color: COLORS.fraud.high }}>
                  {effectiveDecision?.decision || '—'}
                </span>
              </div>
            </div>
          </header>

          {/* Content Area */}
          <main className={`flex-1 overflow-auto p-4 lg:p-6 ${isDark ? 'bg-gray-900' : 'bg-[#f5f7fa]'}`}>
            {caseError && (
              <div className={`mb-4 p-3 rounded border ${isDark ? 'bg-red-900/20 border-red-900/30' : 'bg-red-50 border-red-100'}`}>
                <p className={`text-sm ${isDark ? 'text-red-200' : 'text-red-700'}`}>{caseError}</p>
              </div>
            )}

            {/* VIEW: CASE QUEUE (Default) */}
            {activeView === 'queue' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* LEFT: Context */}
                <div className={`rounded-lg shadow-sm p-5 border ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-medium">Payment Details</h3>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">Mask PII</span>
                      <button onClick={() => setShowPII(!showPII)} className="text-gray-400 hover:text-[#003087]">
                        {showPII ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  {!casePacket?.found || !t ? (
                    <p className="text-sm text-gray-500">No case loaded.</p>
                  ) : (
                    <div className="space-y-5">
                      <DetailRow label="Payment ID" value={t.trans_id} isDark={isDark} />
                      <DetailRow label="Amount" value={`${Number(t.amount).toFixed(2)} USD`} isDark={isDark} highlight />
                      <DetailRow label="Merchant" value={`${t.merchant || '—'}`} isDark={isDark} />
                      <DetailRow
                        label="Customer"
                        value={`${mask(String(t.name || 'User'))} (${mask(String(t.email || ''), 'email')})`}
                        isDark={isDark}
                      />
                      <DetailRow label="Location" value={`${t.country || '—'} (IP: ${t.device_ip || '—'})`} isDark={isDark} />

                      <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
                        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Risk Indicators</h4>
                        <div className="space-y-2">
                          {(effectiveDecision?.rule_hits || []).slice(0, 2).map((rh) => (
                            <RiskBadge key={rh} icon={<AlertTriangle size={14} />} text={rh} color={COLORS.fraud.medium} />
                          ))}
                          {(effectiveDecision?.reason_codes || []).slice(0, 1).map((rc) => (
                            <RiskBadge key={rc} icon={<UserCheck size={14} />} text={rc} color={COLORS.fraud.high} />
                          ))}
                        </div>
                      </div>

                      <div className="pt-2">
                        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Timeline</h4>
                        <TimelineItem color={COLORS.paypal.blue} title="Transaction recorded" time={t.timestamp} isDark={isDark} />
                        <TimelineItem
                          color={COLORS.fraud.high}
                          title="Decision event"
                          time={effectiveDecision ? `Decision: ${effectiveDecision.decision}` : 'Not yet decided'}
                          isDark={isDark}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* CENTER: FraudShield Analysis */}
                <div className={`rounded-lg shadow-sm border overflow-hidden flex flex-col ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <div className={`p-4 border-b flex items-center justify-between ${isDark ? 'border-gray-700 bg-gray-900/50' : 'border-gray-100 bg-gray-50/50'}`}>
                    <div className="flex items-center space-x-3">
                      <div className={`p-1.5 rounded border ${isDark ? 'bg-blue-500/10 border-blue-500/20' : 'bg-white border-slate-200 shadow-sm'}`}>
                        <Cpu className="w-4 h-4 text-[#003087]" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold">FraudShield Analysis</h3>
                        <div className="flex items-center space-x-2 mt-0.5">
                          <span className="text-[10px] bg-blue-100 text-[#003087] px-1.5 rounded-full font-mono">
                            {effectiveDecision?.model_version || 'v0.5.0'}
                          </span>
                          <span className={`text-[10px] ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>AI-Powered</span>
                        </div>
                      </div>
                    </div>
                    {investigationState === 'idle' && (
                      <span className={`text-[10px] text-gray-500 px-2 py-1 rounded border ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200 shadow-sm'}`}>
                        Ready
                      </span>
                    )}
                  </div>

                  <div className="flex-1 p-6 lg:p-8 overflow-y-auto relative">
                    <div className="space-y-6">
                      {/* Score Card */}
                      <div className={`p-4 rounded-lg border ${isDark ? 'bg-gray-700 border-gray-600' : 'bg-gray-50 border-gray-100'}`}>
                        <div className="flex justify-between items-center mb-3">
                          <h4 className="text-sm font-medium">FraudShield Score</h4>
                          <span className="text-lg font-bold" style={{ color: COLORS.fraud.high }}>
                            {effectiveDecision ? `${Math.round(effectiveDecision.risk_score * 100)}/100` : '—'}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2.5 mb-1">
                          <div
                            className="h-2.5 rounded-full transition-all duration-1000"
                            style={{
                              width: `${effectiveDecision ? Math.round(effectiveDecision.risk_score * 100) : 0}%`,
                              background: `linear-gradient(to right, ${COLORS.fraud.low}, ${COLORS.fraud.medium}, ${COLORS.fraud.high})`,
                            }}
                          ></div>
                        </div>
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>Low Risk</span>
                          <span>High Risk</span>
                        </div>
                      </div>

                      {/* Agent Timeline Visualization */}
                      <div className="relative pl-4 mt-6">
                        {/* Vertical Connector */}
                        <div className={`absolute left-8 top-4 bottom-4 w-0.5 ${isDark ? 'bg-gray-700' : 'bg-gray-200'}`}></div>

                        {agents.map((agent, idx) => (
                          <div key={idx} className="relative mb-8 last:mb-0">
                            <div className="flex items-start">
                              {/* Node Icon */}
                              <div
                                className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center z-10 transition-colors duration-500 shadow-sm border ${
                                  agent.status === 'running'
                                    ? 'bg-blue-100 border-blue-200 text-blue-600 animate-pulse'
                                    : agent.status === 'completed'
                                      ? 'bg-green-100 border-green-200 text-green-600'
                                      : isDark
                                        ? 'bg-gray-800 border-gray-600 text-gray-400'
                                        : 'bg-white border-gray-200 text-gray-400'
                                }`}
                              >
                                {agent.status === 'running' ? <Loader2 size={14} className="animate-spin" /> : agent.status === 'completed' ? <Check size={14} /> : agent.icon}
                              </div>

                              <div className="ml-4 flex-1 pt-1">
                                <div className="flex justify-between items-center">
                                  <div>
                                    <h4 className={`text-sm font-bold ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{agent.name}</h4>
                                    <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{agent.status === 'idle' ? 'Waiting to start' : agent.status === 'running' ? 'Processing…' : 'Analysis Complete'}</p>
                                  </div>
                                  {agent.status === 'completed' && <span className="text-xs text-gray-400 font-mono">{agent.duration}</span>}
                                </div>

                                {agent.name === 'Data Collector' && agent.status === 'completed' && (
                                  <div className={`mt-3 rounded p-3 border text-xs font-mono overflow-hidden ${isDark ? 'bg-gray-900 border-gray-700 text-gray-300' : 'bg-white border-gray-200 text-gray-600'}`}>
                                    <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-200 dark:border-gray-600">
                                      <div className="flex items-center gap-2">
                                        <FileJson size={12} className="text-blue-500" />
                                        <span className="font-bold">decision_packet.json</span>
                                      </div>
                                      <Download size={12} className="cursor-pointer hover:text-blue-500" />
                                    </div>
                                    <pre>{JSON.stringify(effectiveDecision || {}, null, 2)}</pre>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* RIGHT: Decision Center */}
                <div className={`rounded-lg shadow-sm p-5 border ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <h3 className="text-lg font-medium mb-4">Decision Center</h3>
                  <div className="space-y-6">
                    <div>
                      <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Recommendations</h4>
                      <div className="space-y-2">
                        <RecommendationCard icon={<AlertTriangle size={16} />} text="Risk signals detected from rules and score" color={COLORS.fraud.high} isDark={isDark} />
                        <RecommendationCard icon={<UserCheck size={16} />} text="Use CHALLENGE for step-up when uncertain" color={COLORS.fraud.medium} isDark={isDark} />
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Final Decision</h4>
                      {investigationState === 'completed' || decisionPacket ? (
                        <div className="grid grid-cols-3 gap-2 mb-4">
                          <ActionButton label="APPROVE" color="green" isDark={isDark} />
                          <ActionButton label="HOLD" color="yellow" isDark={isDark} />
                          <ActionButton label="DENY" color="red" isDark={isDark} />
                        </div>
                      ) : (
                        <div className={`p-4 rounded-lg text-center mb-4 border border-dashed ${isDark ? 'border-gray-700 bg-gray-700/30' : 'border-gray-300 bg-gray-50'}`}>
                          <p className="text-xs text-gray-500">Run decision or investigation to unlock decisions</p>
                        </div>
                      )}
                      <button
                        onClick={runAnalysis}
                        disabled={investigationState === 'running'}
                        className={`w-full py-3 px-4 text-white rounded font-medium flex items-center justify-center transition-all ${investigationState === 'running' ? 'opacity-70 cursor-not-allowed' : 'hover:opacity-90 shadow-md'}`}
                        style={{ backgroundColor: COLORS.paypal.blue }}
                      >
                        {investigationState === 'running' ? (
                          <>
                            <Loader2 size={18} className="animate-spin mr-2" />
                            Analyzing…
                          </>
                        ) : (
                          <>
                            <Play size={18} className="mr-2 fill-current" />
                            {investigationState === 'completed' ? 'Re-Run Analysis' : 'Run Full Analysis'}
                          </>
                        )}
                      </button>
                    </div>
                    <div className={`pt-4 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
                      <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Similar Cases</h4>
                      <div className="space-y-2">
                        {(casePacket?.similar_cases?.similar_cases || []).slice(0, 2).map((c: any) => (
                          <SimilarCase key={c.trans_id} id={c.trans_id} date="—" status={c.reason || 'SIMILAR'} color={COLORS.fraud.medium} isDark={isDark} />
                        ))}
                        {(!casePacket?.similar_cases?.similar_cases || casePacket.similar_cases.similar_cases.length === 0) && (
                          <p className="text-xs text-gray-500">No similar cases available.</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* VIEW: RISK ANALYTICS */}
            {activeView === 'analytics' && (
              <div className="space-y-6">
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => refreshKpis(30)}
                    disabled={kpisLoading}
                    className="px-3 py-2 rounded text-sm font-medium text-white hover:opacity-90 disabled:opacity-70"
                    style={{ backgroundColor: COLORS.paypal.blue }}
                  >
                    {kpisLoading ? 'Loading…' : 'Refresh KPIs'}
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <AnalyticsCard title="Decline Rate" value={kpis ? `${(kpis.decline_rate * 100).toFixed(2)}%` : '—'} change="-0.1%" isDark={isDark} icon={<Activity size={20} />} />
                  <AnalyticsCard title="Challenge Rate" value={kpis ? `${(kpis.challenge_rate * 100).toFixed(2)}%` : '—'} change="+0.2%" isDark={isDark} icon={<AlertTriangle size={20} />} />
                  <AnalyticsCard title="Allow Rate" value={kpis ? `${(kpis.allow_rate * 100).toFixed(2)}%` : '—'} change="+0.1%" isDark={isDark} icon={<CheckCircle size={20} />} />
                </div>

                <div className={`rounded-lg shadow-sm border p-6 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-medium">Portfolio KPIs</h3>
                    <div className="flex gap-2">
                      <span className="text-xs px-2 py-1 rounded border dark:border-gray-600">Last 30 Days</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <DetailRow label="Total Volume" value={kpis ? `${kpis.total_volume.toFixed(2)}` : '—'} isDark={isDark} />
                    <DetailRow label="Chargeback Amount" value={kpis ? `${kpis.chargeback_amount.toFixed(2)}` : '—'} isDark={isDark} />
                    <DetailRow label="Loss Proxy" value={kpis ? `${(kpis.loss_rate_proxy * 100).toFixed(2)}%` : '—'} isDark={isDark} />
                  </div>
                </div>
              </div>
            )}

            {/* VIEW: RULES ENGINE */}
            {activeView === 'rules' && (
              <div className={`rounded-lg shadow-sm border ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                  <h3 className="text-lg font-medium">Active Rule Sets</h3>
                  <button className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
                    <Plus size={16} /> Create Rule
                  </button>
                </div>
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  <RuleRow name="Proxy Signal" id="R-0001" status="Active" trigger="ip_is_proxy == true" action="CHALLENGE" isDark={isDark} />
                  <RuleRow name="High Risk Score" id="R-0002" status="Active" trigger="risk_score >= 0.90" action="DENY" isDark={isDark} />
                  <RuleRow name="Freight Forwarder" id="R-0003" status="Active" trigger="shipping_is_freight_forwarder == true" action="CHALLENGE" isDark={isDark} />
                </div>
              </div>
            )}

            {/* VIEW: TEAM SETTINGS */}
            {activeView === 'team' && (
              <div className={`rounded-lg shadow-sm border ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                  <h3 className="text-lg font-medium">Team Members</h3>
                  <button className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
                    <Plus size={16} /> Invite User
                  </button>
                </div>
                <table className="w-full text-sm text-left">
                  <thead className={`text-xs uppercase ${isDark ? 'bg-gray-900 text-gray-400' : 'bg-gray-50 text-gray-500'}`}>
                    <tr>
                      <th className="px-6 py-3">Name</th>
                      <th className="px-6 py-3">Role</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3">Last Active</th>
                      <th className="px-6 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                    <TeamRow name="Risk Admin" email="admin@fraudshield.ai" role="Administrator" status="Active" lastActive="Now" isDark={isDark} />
                    <TeamRow name="Sarah Chen" email="schen@fraudshield.ai" role="Senior Analyst" status="Active" lastActive="2h ago" isDark={isDark} />
                    <TeamRow name="Mike Ross" email="mross@fraudshield.ai" role="Analyst" status="Away" lastActive="5h ago" isDark={isDark} />
                  </tbody>
                </table>
              </div>
            )}

            {/* VIEW: LLM SETTINGS */}
            {activeView === 'settings' && (
              <div className="max-w-2xl mx-auto space-y-6">
                <div className={`rounded-lg shadow-sm border p-6 ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
                    <div className="p-2 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600">
                      <Key size={24} />
                    </div>
                    <div>
                      <h3 className="text-lg font-medium">API Credentials</h3>
                      <p className="text-xs text-gray-500">Configure API key for secured FraudShield endpoints (optional)</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">X-API-Key</label>
                      <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="(optional)"
                        className={`w-full p-2 rounded border text-sm font-mono ${isDark ? 'bg-gray-700 border-gray-600' : 'bg-white border-gray-300'}`}
                      />
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                      <button
                        onClick={() => setApiKey(getStoredApiKey())}
                        className="px-4 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => setStoredApiKey(apiKey)}
                        className="px-4 py-2 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 flex items-center gap-2"
                      >
                        <Save size={16} /> Save
                      </button>
                    </div>

                    <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                      <p>
                        Note: Investigation requires server-side ops extras (<code>backend[ops]</code>) and an <code>OPENAI_API_KEY</code> set on the backend.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

// --- Subcomponents ---

const NavItem = ({ icon, label, active, isOpen, onClick, className }: any) => (
  <button
    onClick={onClick}
    className={`flex items-center w-full px-4 py-2 text-sm font-medium transition-colors rounded-md mb-1 ${
      active ? 'text-white bg-[#001a6d]' : 'text-blue-100 hover:text-white hover:bg-[#001a6d]/50'
    } ${className}`}
  >
    <div className="w-5 shrink-0">{icon}</div>
    {isOpen && <span className="ml-3 truncate">{label}</span>}
  </button>
);

const DetailRow = ({ label, value, isDark, highlight }: any) => (
  <div>
    <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</h4>
    <p className={`mt-1 text-sm ${highlight ? 'text-xl font-bold' : ''} ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{value}</p>
  </div>
);

const RiskBadge = ({ icon, text, color }: any) => (
  <div className="flex items-center p-2 rounded" style={{ backgroundColor: `${color}1A` }}>
    <div style={{ color: color }} className="mr-2">
      {icon}
    </div>
    <span className="text-sm" style={{ color: color }}>
      {text}
    </span>
  </div>
);

const TimelineItem = ({ color, title, time, isDark }: any) => (
  <div className="flex items-start mt-2">
    <div className="flex-shrink-0 h-4 w-4 mt-0.5 rounded-full" style={{ backgroundColor: color }}></div>
    <div className="ml-3">
      <p className={`text-sm ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{title}</p>
      <p className="text-xs text-gray-500">{time}</p>
    </div>
  </div>
);

const RecommendationCard = ({ icon, text, color, isDark }: any) => (
  <div className={`flex items-start p-3 rounded border ${isDark ? 'bg-gray-700/50 border-gray-600' : 'bg-gray-50 border-gray-200'}`}>
    <div className="mt-0.5 mr-3" style={{ color }}>
      {icon}
    </div>
    <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{text}</span>
  </div>
);

const ActionButton = ({ label, color, isDark }: any) => {
  const colorMap: any = {
    green: {
      bg: isDark ? 'bg-green-900/30' : 'bg-green-100',
      text: isDark ? 'text-green-200' : 'text-green-800',
      border: isDark ? 'border-green-800' : 'border-green-200',
    },
    yellow: {
      bg: isDark ? 'bg-yellow-900/30' : 'bg-yellow-100',
      text: isDark ? 'text-yellow-200' : 'text-yellow-800',
      border: isDark ? 'border-yellow-800' : 'border-yellow-200',
    },
    red: {
      bg: isDark ? 'bg-red-900/30' : 'bg-red-100',
      text: isDark ? 'text-red-200' : 'text-red-800',
      border: isDark ? 'border-red-800' : 'border-red-200',
    },
  };
  const theme = colorMap[color];
  return <button className={`py-2 px-1 text-xs font-bold rounded border hover:opacity-80 transition-opacity ${theme.bg} ${theme.text} ${theme.border}`}>{label}</button>;
};

const SimilarCase = ({ id, date, status, color, isDark }: any) => (
  <div className={`flex items-center justify-between p-2 border-b last:border-0 ${isDark ? 'border-gray-700' : 'border-gray-100'}`}>
    <div>
      <p className={`text-sm font-medium ${isDark ? 'text-gray-300' : 'text-gray-800'}`}>{id}</p>
      <p className="text-xs text-gray-500">{date}</p>
    </div>
    <span className="px-2 py-0.5 text-xs rounded-full text-white font-bold" style={{ backgroundColor: color }}>
      {status}
    </span>
  </div>
);

const AnalyticsCard = ({ title, value, change, isDark, icon }: any) => (
  <div className={`p-5 rounded-lg shadow-sm border ${isDark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
    <div className="flex justify-between items-start mb-2">
      <div className="p-2 rounded bg-blue-50 dark:bg-blue-900/20 text-blue-600">{icon}</div>
      <span className={`text-xs px-1.5 py-0.5 rounded ${change.startsWith('+') ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>{change}</span>
    </div>
    <h4 className="text-sm text-gray-500 dark:text-gray-400 mb-1">{title}</h4>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

const RuleRow = ({ name, id, status, trigger, action, isDark }: any) => (
  <div className="p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
    <div>
      <div className="flex items-center gap-2">
        <h4 className="text-sm font-medium">{name}</h4>
        <span className="text-xs text-gray-400 font-mono">{id}</span>
      </div>
      <div className="flex gap-4 mt-1 text-xs text-gray-500">
        <span>
          Trigger: <span className="font-mono bg-gray-100 dark:bg-gray-700 px-1 rounded">{trigger}</span>
        </span>
        <span>
          Action: <b>{action}</b>
        </span>
      </div>
    </div>
    <div className="flex items-center gap-4">
      <span className={`text-xs px-2 py-1 rounded-full ${status === 'Active' ? 'bg-green-100 text-green-700' : status === 'Inactive' ? 'bg-gray-100 text-gray-500' : 'bg-yellow-100 text-yellow-700'}`}>{status}</span>
      <button className="text-gray-400 hover:text-blue-500">
        <MoreHorizontal size={16} />
      </button>
    </div>
  </div>
);

const TeamRow = ({ name, email, role, status, lastActive, isDark }: any) => (
  <tr className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
    <td className="px-6 py-4">
      <div className="flex items-center">
        <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs">{name.charAt(0)}</div>
        <div className="ml-3">
          <p className="text-sm font-medium">{name}</p>
          <p className="text-xs text-gray-500">{email}</p>
        </div>
      </div>
    </td>
    <td className="px-6 py-4 text-sm">{role}</td>
    <td className="px-6 py-4">
      <span className={`px-2 py-1 text-xs rounded-full ${status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>{status}</span>
    </td>
    <td className="px-6 py-4 text-sm text-gray-500">{lastActive}</td>
    <td className="px-6 py-4">
      <button className="text-gray-400 hover:text-red-500">
        <Trash2 size={16} />
      </button>
    </td>
  </tr>
);
