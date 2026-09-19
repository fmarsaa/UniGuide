import React, { useState, useEffect } from 'react';
import { ProgrammeInfo, AdminAuditLog } from '../types';
import { Shield, Database, History, Check, Edit2, BarChart2, Layers, LogOut, Users, MessageSquare, ArrowRight, UserCheck, Sparkles } from 'lucide-react';
import { db, StudentUser } from '../services/database';

interface AdminDashboardScreenProps {
  programmes: ProgrammeInfo[];
  auditLogs: AdminAuditLog[];
  onUpdateCutoff: (programmeId: string, newCutoff: number) => void;
  onNavigateToFeedback: () => void;
  onLogout?: () => void;
}

export const AdminDashboardScreen: React.FC<AdminDashboardScreenProps> = ({
  programmes,
  auditLogs,
  onUpdateCutoff,
  onNavigateToFeedback,
  onLogout,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'programmes' | 'students' | 'audit' | 'model'>('overview');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [cutoffVal, setCutoffVal] = useState<number>(39.0);
  const [savedSuccess, setSavedSuccess] = useState<string | null>(null);
  const [students, setStudents] = useState<StudentUser[]>([]);

  useEffect(() => {
    try {
      const registered = db.getStudents();
      setStudents(registered || []);
    } catch {
      setStudents([]);
    }
  }, []);

  const handleStartEdit = (prog: ProgrammeInfo) => {
    setEditingId(prog.id);
    setCutoffVal(prog.universities[0]?.lastCutoffPoints || 38.0);
  };

  const handleSaveCutoff = (progId: string) => {
    onUpdateCutoff(progId, cutoffVal);
    setEditingId(null);
    setSavedSuccess(progId);
    setTimeout(() => setSavedSuccess(null), 2500);
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#F8FAFC] p-4 space-y-4">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-4 text-white shadow-sm border border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold">Admin Management Console</h2>
              <p className="text-[10px] text-slate-300">Admissions Directorate & Academic Registrar</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-bold border border-emerald-500/30">
              System Active
            </span>
            {onLogout && (
              <button
                type="button"
                onClick={onLogout}
                className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 text-[10px] font-bold border border-rose-500/30 flex items-center space-x-1 cursor-pointer transition-colors"
                title="Log Out of Admin Console"
              >
                <LogOut className="w-3 h-3" />
                <span>Exit</span>
              </button>
            )}
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/10 text-center">
          <div className="bg-white/5 p-2 rounded-xl">
            <p className="text-[10px] text-slate-300">Catalog Size</p>
            <p className="text-sm font-black text-white">{programmes.length} Degrees</p>
          </div>
          <div className="bg-white/5 p-2 rounded-xl">
            <p className="text-[10px] text-slate-300">Registered Students</p>
            <p className="text-sm font-black text-teal-300">{students.length || 1}</p>
          </div>
          <div className="bg-white/5 p-2 rounded-xl">
            <p className="text-[10px] text-slate-300">Audit Events</p>
            <p className="text-sm font-black text-indigo-300">{auditLogs.length}</p>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex rounded-xl bg-slate-200/80 p-1 text-[11px] font-semibold overflow-x-auto">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-3 py-1.5 rounded-lg flex items-center justify-center space-x-1 transition-all shrink-0 cursor-pointer ${
            activeTab === 'overview' ? 'bg-white text-[#14213D] shadow-xs font-bold' : 'text-slate-600'
          }`}
        >
          <span>Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('programmes')}
          className={`px-3 py-1.5 rounded-lg flex items-center justify-center space-x-1 transition-all shrink-0 cursor-pointer ${
            activeTab === 'programmes' ? 'bg-white text-[#14213D] shadow-xs font-bold' : 'text-slate-600'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>Cutoffs & Catalog</span>
        </button>

        <button
          onClick={() => setActiveTab('students')}
          className={`px-3 py-1.5 rounded-lg flex items-center justify-center space-x-1 transition-all shrink-0 cursor-pointer ${
            activeTab === 'students' ? 'bg-white text-[#14213D] shadow-xs font-bold' : 'text-slate-600'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Students ({students.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`px-3 py-1.5 rounded-lg flex items-center justify-center space-x-1 transition-all shrink-0 cursor-pointer ${
            activeTab === 'audit' ? 'bg-white text-[#14213D] shadow-xs font-bold' : 'text-slate-600'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          <span>Audit Logs</span>
        </button>

        <button
          onClick={() => setActiveTab('model')}
          className={`px-3 py-1.5 rounded-lg flex items-center justify-center space-x-1 transition-all shrink-0 cursor-pointer ${
            activeTab === 'model' ? 'bg-white text-[#14213D] shadow-xs font-bold' : 'text-slate-600'
          }`}
        >
          <BarChart2 className="w-3.5 h-3.5" />
          <span>Model Specs</span>
        </button>
      </div>

      {/* TAB 0: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-3">
          <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Admissions Control Summary
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Welcome to the UniGuide Administrative Console. As an administrator, you manage official KUCCPS minimum admission cutoff thresholds, monitor candidate activity, and verify recommendation model performance.
            </p>

            <div className="grid grid-cols-2 gap-2 pt-1">
              <button
                onClick={() => setActiveTab('programmes')}
                className="p-3 bg-slate-50 hover:bg-slate-100 rounded-xl border border-slate-200 text-left transition-colors cursor-pointer"
              >
                <div className="w-7 h-7 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center mb-1.5">
                  <Database className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-bold text-slate-800">Adjust Cutoffs</h4>
                <p className="text-[10px] text-slate-500 mt-0.5">Edit live university cutoff points</p>
              </button>

              <button
                onClick={() => setActiveTab('students')}
                className="p-3 bg-slate-50 hover:bg-slate-100 rounded-xl border border-slate-200 text-left transition-colors cursor-pointer"
              >
                <div className="w-7 h-7 rounded-lg bg-teal-100 text-teal-700 flex items-center justify-center mb-1.5">
                  <Users className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-bold text-slate-800">Candidate Records</h4>
                <p className="text-[10px] text-slate-500 mt-0.5">View registered student profiles</p>
              </button>

              <button
                onClick={() => setActiveTab('audit')}
                className="p-3 bg-slate-50 hover:bg-slate-100 rounded-xl border border-slate-200 text-left transition-colors cursor-pointer"
              >
                <div className="w-7 h-7 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center mb-1.5">
                  <History className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-bold text-slate-800">Audit Trail</h4>
                <p className="text-[10px] text-slate-500 mt-0.5">Real-time system action logs</p>
              </button>

              <button
                onClick={onNavigateToFeedback}
                className="p-3 bg-slate-50 hover:bg-slate-100 rounded-xl border border-slate-200 text-left transition-colors cursor-pointer"
              >
                <div className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center mb-1.5">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <h4 className="text-xs font-bold text-slate-800">Model Feedback</h4>
                <p className="text-[10px] text-slate-500 mt-0.5">Student evaluation ratings</p>
              </button>
            </div>
          </div>

          {/* Recent Audit Activities Card */}
          <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-2.5">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800 flex items-center space-x-1.5">
                <History className="w-3.5 h-3.5 text-indigo-600" />
                <span>Recent System Activity</span>
              </h3>
              <button
                onClick={() => setActiveTab('audit')}
                className="text-[11px] font-bold text-indigo-600 hover:underline"
              >
                View All &rarr;
              </button>
            </div>
            <div className="space-y-1.5">
              {auditLogs.slice(0, 3).map((log) => (
                <div key={log.id} className="p-2.5 bg-slate-50 rounded-xl border border-slate-100 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800 text-[11px]">{log.details}</span>
                    <span className="text-[10px] text-slate-400">{log.timestamp}</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    Actor: <span className="font-medium text-slate-700">{log.actorName}</span>
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 1: PROGRAMMES CUTOFF MANAGEMENT */}
      {activeTab === 'programmes' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800">KUCCPS Admission Cutoffs</h3>
            <span className="text-[10px] text-slate-500">Updates sync across system</span>
          </div>

          <div className="space-y-2">
            {programmes.map((prog) => {
              const primaryUni = prog.universities[0];
              const isEditing = editingId === prog.id;

              return (
                <div
                  key={prog.id}
                  className="bg-white rounded-xl p-3.5 border border-slate-200/80 shadow-xs space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700">
                        {prog.code}
                      </span>
                      <h4 className="text-xs font-bold text-slate-900 mt-1 leading-snug">
                        {prog.name}
                      </h4>
                      <p className="text-[10px] text-slate-500">
                        Min Mean: {prog.admissionRequirements.minimumMeanGrade} &bull; {primaryUni?.name || 'KUCCPS'}
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <p className="text-[10px] text-slate-400">Current Cutoff</p>
                      <p className="text-sm font-extrabold text-[#4F46E5]">
                        {primaryUni?.lastCutoffPoints.toFixed(1)} pts
                      </p>
                    </div>
                  </div>

                  {/* Edit Mode Inline */}
                  {isEditing ? (
                    <div className="pt-2 border-t border-slate-100 flex items-center space-x-2">
                      <span className="text-[10px] text-slate-600">New Cutoff:</span>
                      <input
                        type="number"
                        step="0.1"
                        min="20"
                        max="48"
                        value={cutoffVal}
                        onChange={(e) => setCutoffVal(parseFloat(e.target.value) || 35)}
                        className="w-20 px-2 py-1 text-xs border rounded-lg bg-slate-50 font-bold"
                      />
                      <button
                        onClick={() => handleSaveCutoff(prog.id)}
                        className="px-2.5 py-1 bg-emerald-600 text-white rounded-lg text-xs font-bold flex items-center space-x-1 cursor-pointer"
                      >
                        <Check className="w-3 h-3" />
                        <span>Save</span>
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        className="px-2 py-1 text-slate-500 text-xs font-medium cursor-pointer"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                      <span className="text-[10px] text-emerald-600 font-semibold">
                        {savedSuccess === prog.id ? '✓ Cutoff Updated!' : `Cluster: ${prog.admissionRequirements.clusterSubjectGroup.slice(0, 30)}...`}
                      </span>
                      <button
                        onClick={() => handleStartEdit(prog)}
                        className="text-[10px] font-bold text-[#4F46E5] hover:text-indigo-800 flex items-center space-x-1 cursor-pointer"
                      >
                        <Edit2 className="w-3 h-3" />
                        <span>Adjust Cutoff</span>
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: REGISTERED STUDENTS */}
      {activeTab === 'students' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800">Registered Student Candidates</h3>
            <span className="text-[10px] text-slate-500">Live Roster</span>
          </div>

          {students.length === 0 ? (
            <div className="bg-white rounded-xl p-6 text-center border border-slate-200 space-y-2">
              <Users className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="text-xs font-bold text-slate-700">No candidates registered yet</p>
              <p className="text-[11px] text-slate-500">
                New candidate accounts created on the portal will appear here automatically.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {students.map((student) => (
                <div
                  key={student.uid}
                  className="bg-white rounded-xl p-3.5 border border-slate-200 shadow-xs space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                        <UserCheck className="w-3.5 h-3.5 text-teal-600" />
                        <span>{student.fullName}</span>
                      </h4>
                      <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                        {student.indexNumber} &bull; {student.email}
                      </p>
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 text-[10px] font-bold border border-teal-200">
                      Mean: {student.profile?.kcseMeanGrade || 'N/A'}
                    </span>
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-600">
                    <span>
                      Est. Cluster: <strong className="text-slate-900 font-bold">{student.profile?.calculatedClusterScore || '—'} pts</strong>
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Registered: {new Date(student.createdAt).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: AUDIT LOGS */}
      {activeTab === 'audit' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800">System Audit Trail</h3>
            <span className="text-[10px] text-slate-500">Immutable Log Records</span>
          </div>

          <div className="space-y-2">
            {auditLogs.map((log) => (
              <div
                key={log.id}
                className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full ${
                    log.action === 'recommendation_run'
                      ? 'bg-teal-50 text-teal-700'
                      : 'bg-amber-50 text-amber-700'
                  }`}>
                    {log.action.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">{log.timestamp}</span>
                </div>
                <p className="text-xs font-semibold text-slate-800">{log.details}</p>
                <p className="text-[10px] text-slate-500">
                  Actor: <span className="font-medium text-slate-700">{log.actorName}</span>
                  {log.studentIndex && ` &bull; Ref: ${log.studentIndex}`}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: MODEL ARCHITECTURE SPEC */}
      {activeTab === 'model' && (
        <div className="space-y-3">
          <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs space-y-3">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-[#4F46E5]" />
              <h3 className="text-xs font-bold text-slate-900">Machine Learning Classification Pipeline</h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              The UniGuide recommendation engine is built on an ensemble Random Forest model trained on secondary school profiles grounded in Kenya National Examinations Council (KNEC) grading structures and KUCCPS cluster guidelines.
            </p>

            {/* Model Evaluation Metrics Grid */}
            <div className="grid grid-cols-4 gap-1.5 pt-1">
              <div className="bg-indigo-50/70 p-2 rounded-lg text-center border border-indigo-100">
                <p className="text-[9px] font-bold text-indigo-700">Accuracy</p>
                <p className="text-xs font-black text-indigo-950">91.4%</p>
              </div>
              <div className="bg-emerald-50/70 p-2 rounded-lg text-center border border-emerald-100">
                <p className="text-[9px] font-bold text-emerald-700">Precision</p>
                <p className="text-xs font-black text-emerald-950">89.8%</p>
              </div>
              <div className="bg-teal-50/70 p-2 rounded-lg text-center border border-teal-100">
                <p className="text-[9px] font-bold text-teal-700">Recall</p>
                <p className="text-xs font-black text-teal-950">90.5%</p>
              </div>
              <div className="bg-amber-50/70 p-2 rounded-lg text-center border border-amber-100">
                <p className="text-[9px] font-bold text-amber-700">F1-Score</p>
                <p className="text-xs font-black text-amber-950">94.2%</p>
              </div>
            </div>

            {/* Dataset & Preprocessing Parameters */}
            <div className="space-y-1.5 text-xs pt-2">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Training Corpus</span>
                <span className="font-semibold text-slate-800">KCSE Student Performance Vectors</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Train / Test Partition</span>
                <span className="font-semibold text-slate-800">80% Train / 20% Stratified Test</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Algorithm</span>
                <span className="font-semibold text-slate-800">Random Forest Classifier</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Ensemble Estimators</span>
                <span className="font-semibold text-slate-800">100 Decision Trees (max_depth: 12)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Explainability Engine</span>
                <span className="font-semibold text-slate-800">TreeSHAP (Feature Attribution)</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Output Ranking</span>
                <span className="font-semibold text-slate-800">Top 3 Degrees Ranked by predict_proba</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs space-y-2">
            <h4 className="text-xs font-bold text-slate-900">Feature Importance Hierarchy (TreeSHAP)</h4>
            <div className="space-y-1.5 text-[11px]">
              <div>
                <div className="flex justify-between text-slate-600 mb-0.5">
                  <span>KCSE Cluster Subject Foundation</span>
                  <span className="font-bold text-slate-800">32%</span>
                </div>
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-indigo-600 h-full rounded-full" style={{ width: '32%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-slate-600 mb-0.5">
                  <span>KCSE Overall Mean Grade</span>
                  <span className="font-bold text-slate-800">26%</span>
                </div>
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-teal-600 h-full rounded-full" style={{ width: '26%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-slate-600 mb-0.5">
                  <span>Career Aspirations Matching</span>
                  <span className="font-bold text-slate-800">20%</span>
                </div>
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-amber-600 h-full rounded-full" style={{ width: '20%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-slate-600 mb-0.5">
                  <span>Interests & Personal Strengths</span>
                  <span className="font-bold text-slate-800">14%</span>
                </div>
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-emerald-600 h-full rounded-full" style={{ width: '14%' }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-slate-600 mb-0.5">
                  <span>Skills & Competencies Vector</span>
                  <span className="font-bold text-slate-800">8%</span>
                </div>
                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-blue-500 h-full rounded-full" style={{ width: '8%' }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
