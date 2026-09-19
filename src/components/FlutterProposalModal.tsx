import React from 'react';
import { X, Smartphone, Code2, Cpu, Database, CheckCircle2, Terminal, Layers } from 'lucide-react';

interface FlutterProposalModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FlutterProposalModal: React.FC<FlutterProposalModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-[#0F172A] border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-[#14213D] px-6 py-4 flex items-center justify-between border-b border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#0EA5A4] to-[#4F46E5] flex items-center justify-center text-white shadow-md">
              <Smartphone className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <span>UniGuide: Flutter Mobile Architecture</span>
                <span className="text-[10px] bg-teal-500/20 text-teal-300 px-2 py-0.5 rounded-full border border-teal-500/30">
                  Android Target
                </span>
              </h2>
              <p className="text-xs text-slate-300">
                KUCCPS Decision Support System • Mobile Architecture
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center cursor-pointer transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm text-slate-200">
          {/* Overview Note */}
          <div className="p-4 rounded-xl bg-teal-950/40 border border-teal-800/60 text-teal-100 flex items-start space-x-3">
            <CheckCircle2 className="w-5 h-5 text-teal-400 shrink-0 mt-0.5" />
            <div className="text-xs leading-relaxed">
              <strong className="text-teal-200 block text-sm mb-1">
                Native Flutter Android & FastAPI Backend Generated
              </strong>
              This application is designed specifically as an <strong>Android Flutter Mobile Application</strong> adhering to the Strathmore University proposal requirements. The live preview operates as an interactive Android device viewport, while the complete <strong>Flutter (Dart)</strong> project and <strong>FastAPI / Random Forest ML</strong> backend files are included directly in your repository.
            </div>
          </div>

          {/* Wireframes to Code Mapping */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Proposal Wireframe Implementation Matrix (Figures 4.6 – 4.11)</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                <span className="font-semibold text-teal-300 block">Figure 4.6: Authentication</span>
                <span className="text-slate-400 text-[11px] block mb-1">Student & Admin Firebase Auth</span>
                <code className="text-[10px] text-indigo-300 bg-slate-900 px-1.5 py-0.5 rounded">
                  flutter_app/lib/screens/auth_screen.dart
                </code>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                <span className="font-semibold text-teal-300 block">Figure 4.7: Profile Setup</span>
                <span className="text-slate-400 text-[11px] block mb-1">KCSE Grades, Interests, Skills, Strengths</span>
                <code className="text-[10px] text-indigo-300 bg-slate-900 px-1.5 py-0.5 rounded">
                  flutter_app/lib/screens/profile_setup_screen.dart
                </code>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                <span className="font-semibold text-teal-300 block">Figure 4.8: Recommendation Screen</span>
                <span className="text-slate-400 text-[11px] block mb-1">Top 3 Ranked Courses, Confidence %, SHAP</span>
                <code className="text-[10px] text-indigo-300 bg-slate-900 px-1.5 py-0.5 rounded">
                  flutter_app/lib/screens/recommendations_screen.dart
                </code>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                <span className="font-semibold text-teal-300 block">Figure 4.9: Programme Details</span>
                <span className="text-slate-400 text-[11px] block mb-1">Requirements, Cutoffs, Unis, Careers</span>
                <code className="text-[10px] text-indigo-300 bg-slate-900 px-1.5 py-0.5 rounded">
                  flutter_app/lib/screens/programme_detail_screen.dart
                </code>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                <span className="font-semibold text-teal-300 block">Figure 4.10: Admin Dashboard</span>
                <span className="text-slate-400 text-[11px] block mb-1">Manage Cutoffs, Audit Trails (DR-06)</span>
                <code className="text-[10px] text-indigo-300 bg-slate-900 px-1.5 py-0.5 rounded">
                  flutter_app/lib/screens/admin_dashboard_screen.dart
                </code>
              </div>

              <div className="p-3 rounded-lg bg-slate-800/80 border border-slate-700">
                <span className="font-semibold text-teal-300 block">Figure 4.11: Rating & Feedback</span>
                <span className="text-slate-400 text-[11px] block mb-1">5-Star Rating & Firestore Submission</span>
                <code className="text-[10px] text-indigo-300 bg-slate-900 px-1.5 py-0.5 rounded">
                  flutter_app/lib/screens/feedback_dialog.dart
                </code>
              </div>
            </div>
          </div>

          {/* Backend & ML Model */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-teal-400" />
              <span>Machine Learning & FastAPI Backend (/backend)</span>
            </h3>
            <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-300 font-medium">Scikit-Learn Random Forest Classifier:</span>
                <span className="text-teal-400 font-mono text-[11px]">150 Trees, Stratified 80/20</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-300 font-medium">Explainability Algorithm:</span>
                <span className="text-indigo-400 font-mono text-[11px]">SHAP (TreeExplainer)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-300 font-medium">FastAPI Server:</span>
                <span className="text-amber-400 font-mono text-[11px]">POST /api/recommend, POST /api/feedback</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-300 font-medium">Synthetic Dataset Pipeline:</span>
                <span className="text-emerald-400 font-mono text-[11px]">synthetic_data_generator.py (N=1500)</span>
              </div>
            </div>
          </div>

          {/* Running on Android */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center space-x-2">
              <Terminal className="w-4 h-4 text-amber-400" />
              <span>How to Run the Flutter Codebase in Android Studio</span>
            </h3>
            <div className="bg-slate-950 p-3 rounded-lg font-mono text-[11px] text-slate-300 border border-slate-800 space-y-1">
              <p className="text-slate-500"># 1. Open /flutter_app in Android Studio or terminal</p>
              <p className="text-teal-400">cd flutter_app</p>
              <p className="text-teal-400">flutter pub get</p>
              <p className="text-slate-500"># 2. Run on connected Android phone or emulator</p>
              <p className="text-teal-400">flutter run</p>
              <p className="text-slate-500"># 3. Build release APK for Android</p>
              <p className="text-teal-400">flutter build apk --release</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-[#14213D] px-6 py-3 border-t border-slate-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-[#0EA5A4] hover:bg-[#0EA5A4]/90 text-white text-xs font-semibold cursor-pointer transition-colors"
          >
            Close Architecture Guide
          </button>
        </div>
      </div>
    </div>
  );
};
