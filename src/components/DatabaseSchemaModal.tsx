import React, { useState } from 'react';
import { X, Database, Shield, User, BookOpen, Layers, CheckCircle2, ArrowRight, Sparkles, Star } from 'lucide-react';
import { db } from '../services/database';

interface DatabaseSchemaModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DatabaseSchemaModal: React.FC<DatabaseSchemaModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState<'overview' | 'admins' | 'students' | 'programmes'>('overview');
  const schemaInfo = db.getDatabaseSchemaDetails();
  const currentAdmins = db.getAdmins();
  const currentStudents = db.getStudents();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 bg-black/60 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white text-slate-900 rounded-2xl w-full max-w-sm max-h-[85vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="bg-[#14213D] text-white p-4 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-teal-500/20 text-teal-300 flex items-center justify-center">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold leading-tight">Database Architecture</h3>
              <p className="text-[10px] text-teal-300">Firebase: tenacious-sentry-fv9wh &bull; Firestore Linked</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-slate-300 hover:text-white cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Collection Selector Tabs */}
        <div className="flex border-b border-slate-200 bg-slate-50 text-[11px] font-semibold shrink-0">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex-1 py-2 text-center transition-colors cursor-pointer ${
              activeTab === 'overview' ? 'border-b-2 border-indigo-600 text-indigo-700 bg-white' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('admins')}
            className={`flex-1 py-2 text-center transition-colors cursor-pointer ${
              activeTab === 'admins' ? 'border-b-2 border-amber-600 text-amber-700 bg-white' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            /admins
          </button>
          <button
            onClick={() => setActiveTab('students')}
            className={`flex-1 py-2 text-center transition-colors cursor-pointer ${
              activeTab === 'students' ? 'border-b-2 border-teal-600 text-teal-700 bg-white' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            /students
          </button>
          <button
            onClick={() => setActiveTab('programmes')}
            className={`flex-1 py-2 text-center transition-colors cursor-pointer ${
              activeTab === 'programmes' ? 'border-b-2 border-blue-600 text-blue-700 bg-white' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            /programmes
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs text-slate-600">
          {activeTab === 'overview' && (
            <div className="space-y-3">
              <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-3 space-y-1.5">
                <p className="font-bold text-indigo-950 text-xs flex items-center space-x-1.5">
                  <Database className="w-3.5 h-3.5 text-indigo-600" />
                  <span>How the UniGuide Database Works</span>
                </p>
                <p className="text-[11px] text-slate-700 leading-relaxed">
                  UniGuide uses a <strong>NoSQL Cloud Firestore</strong> database model with <strong>3 top-level collections</strong>. Authentication is unified: when any user signs in with their email, the database queries these collections to identify their role instantly:
                </p>
              </div>

              <div className="space-y-2">
                <div className="p-2.5 rounded-xl border border-amber-200 bg-amber-50/50 flex items-start space-x-2">
                  <Shield className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-amber-950 text-[11px]">1. /admins Collection</p>
                    <p className="text-[10px] text-slate-600">
                      Stores pre-provisioned university faculty accounts (<code className="font-mono text-amber-800 font-bold">admin@strathmore.edu</code>). When this email logs in, the database matches this collection and automatically grants <strong>Administrator Console</strong> access.
                    </p>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl border border-teal-200 bg-teal-50/50 flex items-start space-x-2">
                  <User className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-teal-950 text-[11px]">2. /students Collection</p>
                    <p className="text-[10px] text-slate-600">
                      Stores high school leavers. When a new student signs up, a document is created here with role <code className="font-mono text-teal-800 font-bold">'student'</code>, routing them to input their KCSE grades and preferences.
                    </p>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl border border-blue-200 bg-blue-50/50 flex items-start space-x-2">
                  <BookOpen className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold text-blue-950 text-[11px]">3. /programmes Collection</p>
                    <p className="text-[10px] text-slate-600">
                      Stores accredited degree programmes, cutoff cluster weights, prerequisites, and embedded audit records documenting admin changes.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 text-[10px] text-slate-500">
                <p className="font-semibold text-slate-700 mb-1">Subcollection Nesting (Figure 4.5):</p>
                <p>
                  Each student document in <code className="text-indigo-600 font-mono">/students/{'{uid}'}</code> has two subcollections: <code className="text-teal-700 font-mono">/recommendations</code> (stores Top 3 predictions & SHAP maps) and <code className="text-amber-700 font-mono">/feedback</code> (stores user satisfaction ratings).
                </p>
              </div>
            </div>
          )}

          {activeTab === 'admins' && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 text-xs">Admins Collection Schema</span>
                <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold">
                  {currentAdmins.length} Stored in Database
                </span>
              </div>
              <p className="text-[11px] text-slate-600">
                These email records exist directly in the database. Logging in with these credentials immediately yields administrator privileges.
              </p>

              <div className="space-y-1.5">
                {currentAdmins.map((admin) => (
                  <div key={admin.uid} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1 font-mono text-[10px]">
                    <div className="flex justify-between items-center text-slate-900 font-bold">
                      <span>{admin.email}</span>
                      <span className="px-1.5 py-0.5 rounded bg-amber-500 text-white text-[9px]">role: {admin.role}</span>
                    </div>
                    <p className="text-slate-600 font-sans text-[10px]">{admin.fullName} &bull; {admin.faculty}</p>
                    <p className="text-slate-400 text-[9px]">uid: {admin.uid}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'students' && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 text-xs">Students Collection Schema</span>
                <span className="px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 text-[10px] font-bold">
                  {currentStudents.length} Registered
                </span>
              </div>
              <p className="text-[11px] text-slate-600">
                Created during student Sign Up. Embeds profile attributes, KCSE grades, and parent-links to recommendation and feedback subcollections.
              </p>

              <div className="space-y-1.5">
                {currentStudents.map((st) => (
                  <div key={st.uid} className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1 font-mono text-[10px]">
                    <div className="flex justify-between items-center text-slate-900 font-bold">
                      <span>{st.email}</span>
                      <span className="px-1.5 py-0.5 rounded bg-teal-600 text-white text-[9px]">role: {st.role}</span>
                    </div>
                    <p className="text-slate-600 font-sans text-[10px]">{st.fullName} &bull; Index: {st.indexNumber}</p>
                    <div className="flex items-center space-x-2 text-[9px] text-slate-500 font-sans pt-0.5">
                      <span>Mean: {st.profile?.kcseMeanGrade || 'N/A'}</span>
                      <span>Cluster: {st.profile?.calculatedClusterScore || 'N/A'} pts</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'programmes' && (
            <div className="space-y-2.5">
              <span className="font-bold text-slate-900 text-xs">Programmes Repository Schema</span>
              <p className="text-[11px] text-slate-600">
                Top-level collection holding all degree offerings, prerequisite grades, cluster cutoffs across Kenyan universities, and embedded audit logs for administrative modifications.
              </p>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1 text-[10px] font-mono">
                <p className="text-indigo-900 font-bold font-sans">Document Structure:</p>
                <p>id: "prog-cs"</p>
                <p>name: "Bachelor of Science in Computer Science"</p>
                <p>code: "12301"</p>
                <p>admissionRequirements: &#123; minMean: "C+", requiredSubjects: [...] &#125;</p>
                <p>universities: [Strathmore, UoN, JKUAT, KU, Moi]</p>
                <p>auditLogs: [&#123; action, timestamp, actor &#125;]</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 shrink-0">
          <button
            onClick={onClose}
            className="w-full py-2 bg-[#14213D] text-white rounded-xl text-xs font-bold hover:bg-slate-800 transition-colors cursor-pointer"
          >
            Close Schema Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
