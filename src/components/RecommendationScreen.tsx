import React from 'react';
import { RecommendationResult, ProgrammeInfo } from '../types';
import { 
  Sparkles, Bookmark, BookmarkCheck, ChevronRight, HelpCircle, 
  Building2, CheckCircle2, AlertCircle, MessageSquare, Sliders, 
  Database, Calculator, GraduationCap, ShieldCheck, ShieldAlert 
} from 'lucide-react';

interface RecommendationScreenProps {
  results: RecommendationResult[];
  savedIds: string[];
  userEstimatedCluster?: number;
  onToggleSave: (id: string) => void;
  onOpenShap: (result: RecommendationResult) => void;
  onOpenDetails: (programme: ProgrammeInfo) => void;
  onNavigateToProfile: () => void;
  onNavigateToFeedback: (programmeId?: string) => void;
}

export const RecommendationScreen: React.FC<RecommendationScreenProps> = ({
  results,
  savedIds,
  userEstimatedCluster = 41.8,
  onToggleSave,
  onOpenShap,
  onOpenDetails,
  onNavigateToProfile,
  onNavigateToFeedback,
}) => {
  if (!results || results.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-4 bg-[#F8FAFC]">
        <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-[#4F46E5] flex items-center justify-center shadow-inner">
          <Sparkles className="w-8 h-8" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-900">No Recommendations Yet</h2>
          <p className="text-xs text-slate-500 max-w-xs mx-auto mt-1 leading-relaxed">
            Please fill in your KCSE academic results and career interests in the profile section to run the KUCCPS-aligned Machine Learning model.
          </p>
        </div>
        <button
          onClick={onNavigateToProfile}
          className="py-2.5 px-5 bg-[#4F46E5] text-white rounded-xl text-xs font-bold shadow-md hover:bg-indigo-700 transition-all cursor-pointer"
        >
          Setup Student Profile
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-[#F8FAFC] p-4 space-y-3.5">
      {/* Top Banner Info */}
      <div className="bg-white rounded-2xl p-3.5 border border-slate-200/80 shadow-xs space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="inline-flex items-center space-x-1.5 text-[10px] font-bold text-emerald-700 uppercase tracking-wider bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/60">
            <GraduationCap className="w-3.5 h-3.5" />
            <span>Official KUCCPS Verified Criteria</span>
          </div>
        </div>

        <div>
          <h2 className="text-sm font-black text-slate-900 leading-tight">
            Top 3 Degree Recommendations
          </h2>
          <p className="text-[11px] text-slate-600 leading-snug mt-0.5">
            Verified accredited Kenyan university programmes evaluated with authentic KUCCPS Cluster Weighted Points: <code className="bg-slate-100 px-1 py-0.5 rounded text-[10px] font-mono text-indigo-700 font-semibold">C = √((r/48) × (t/84)) × 48</code>.
          </p>
        </div>

        <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
          <div className="flex items-center space-x-1.5 text-slate-600">
            <Calculator className="w-3.5 h-3.5 text-indigo-600" />
            <span>
              Candidate Base Cluster: <strong className="text-slate-900 font-bold">{userEstimatedCluster} pts</strong>
            </span>
          </div>
          <button
            onClick={onNavigateToProfile}
            className="text-[10px] font-bold text-[#4F46E5] hover:underline flex items-center space-x-1"
          >
            <Sliders className="w-3 h-3" />
            <span>Adjust KCSE Grades</span>
          </button>
        </div>
      </div>

      {/* Top 3 Recommendation Cards */}
      <div className="space-y-3">
        {results.map((item) => {
          const isSaved = savedIds.includes(item.programme.id);
          const primaryUni = item.programme.universities[0];
          const isEligible = (item.calculatedClusterScore || userEstimatedCluster) >= (item.targetCutoff || primaryUni?.lastCutoffPoints || 38);

          const rankBadge =
            item.rank === 1
              ? { bg: 'bg-gradient-to-r from-amber-500 to-amber-600', text: '#1 Top Recommendation' }
              : item.rank === 2
              ? { bg: 'bg-gradient-to-r from-indigo-600 to-indigo-700', text: '#2 Secondary Choice' }
              : { bg: 'bg-gradient-to-r from-[#0EA5A4] to-teal-700', text: '#3 Alternative Option' };

          return (
            <div
              key={item.programmeId}
              id={`recommendation-card-${item.programmeId}`}
              className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden transition-all hover:shadow-sm"
            >
              {/* Card Header Pill */}
              <div className="px-4 pt-3.5 pb-2 flex items-center justify-between border-b border-slate-100">
                <div className="flex items-center space-x-2">
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold text-white shadow-xs ${rankBadge.bg}`}>
                    {rankBadge.text}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono font-bold bg-slate-100 px-1.5 py-0.5 rounded">
                    Code: {item.programme.code}
                  </span>
                </div>

                {/* Bookmark Toggle */}
                <button
                  onClick={() => onToggleSave(item.programme.id)}
                  className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
                    isSaved ? 'text-amber-500 bg-amber-50' : 'text-slate-400 hover:text-slate-600'
                  }`}
                  title={isSaved ? 'Remove from Saved' : 'Save Programme'}
                >
                  {isSaved ? <BookmarkCheck className="w-4 h-4 fill-amber-500" /> : <Bookmark className="w-4 h-4" />}
                </button>
              </div>

              {/* Card Body */}
              <div className="p-4 space-y-3">
                <div>
                  <h3 className="text-xs font-black text-slate-900 leading-snug">
                    {item.programme.name}
                  </h3>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    {item.programme.faculty} &bull; {item.clusterGroupCode || item.programme.category}
                  </p>
                </div>

                {/* Cluster Points Detailed Breakdown Grid */}
                <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/60 space-y-2 text-xs">
                  <div className="grid grid-cols-3 gap-2 pb-2 border-b border-slate-200/60 text-center">
                    <div>
                      <span className="text-[9px] text-slate-500 uppercase tracking-wider block">Your CWP</span>
                      <span className="text-xs font-black text-indigo-700 font-mono">
                        {(item.calculatedClusterScore || userEstimatedCluster).toFixed(3)}
                      </span>
                    </div>

                    <div>
                      <span className="text-[9px] text-slate-500 uppercase tracking-wider block">Cutoff (UoN/JKUAT)</span>
                      <span className="text-xs font-black text-slate-800 font-mono">
                        {(item.targetCutoff || primaryUni?.lastCutoffPoints || 38.0).toFixed(1)}
                      </span>
                    </div>

                    <div>
                      <span className="text-[9px] text-slate-500 uppercase tracking-wider block">Compatibility</span>
                      <span className="text-xs font-black text-emerald-700 font-mono">
                        {item.confidence.toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Cutoff Status and Offering Universities */}
                  <div className="flex items-center justify-between text-[11px] pt-0.5">
                    <div className="flex items-center space-x-1.5">
                      {isEligible ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      ) : (
                        <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      )}
                      <span className={`font-bold ${isEligible ? 'text-emerald-700' : 'text-amber-700'}`}>
                        {isEligible
                          ? `Eligible (+${(item.cutoffDifference || 0).toFixed(2)} pts)`
                          : `Below Cutoff (${(item.cutoffDifference || 0).toFixed(2)} pts)`}
                      </span>
                    </div>

                    <span className="text-[10px] text-slate-500 font-medium">
                      {item.qualifiedUniversitiesCount !== undefined
                        ? `${item.qualifiedUniversitiesCount}/${item.totalUniversitiesOffering || item.programme.universities.length} Univs Qualified`
                        : `${item.programme.universities.length} Univs in Kenya`}
                    </span>
                  </div>

                  {/* Cluster 4 Subjects pill preview */}
                  {item.clusterSubjectBreakdown && item.clusterSubjectBreakdown.length > 0 && (
                    <div className="text-[10px] text-slate-600 bg-white/90 p-1.5 rounded-lg border border-slate-200/50">
                      <span className="font-semibold text-slate-700">Cluster Subjects: </span>
                      {item.clusterSubjectBreakdown.map((s, idx) => (
                        <span key={idx} className="font-mono text-slate-600">
                          {s.subject} ({s.grade})
                          {idx < item.clusterSubjectBreakdown.length - 1 ? ', ' : ''}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Prominent Subject Prerequisite Disclaimer Banner */}
                {item.prerequisitesMet !== undefined && (
                  <div className={`p-2.5 rounded-xl border text-[11px] space-y-1.5 ${
                    item.prerequisitesMet
                      ? 'bg-emerald-500/10 border-emerald-300 text-emerald-950'
                      : 'bg-rose-500/10 border-rose-300 text-rose-950'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-1.5 font-black text-xs">
                        {item.prerequisitesMet ? (
                          <>
                            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                            <span className="text-emerald-800">KUCCPS Subject Prerequisites Satisfied</span>
                          </>
                        ) : (
                          <>
                            <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
                            <span className="text-rose-800">Prerequisite Shortfall Detected</span>
                          </>
                        )}
                      </div>
                      <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold uppercase tracking-wider ${
                        item.prerequisitesMet
                          ? 'bg-emerald-600 text-white'
                          : 'bg-rose-600 text-white'
                      }`}>
                        {item.prerequisitesMet ? 'Prereqs Met' : 'Action Required'}
                      </span>
                    </div>

                    {!item.prerequisitesMet && item.missingPrerequisites && item.missingPrerequisites.length > 0 && (
                      <div className="space-y-1 pt-0.5">
                        <p className="text-[10px] text-rose-800 font-semibold">
                          KUCCPS hard minimum subject requirements not satisfied:
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {item.missingPrerequisites.map((m, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded-md bg-white border border-rose-300 text-rose-700 text-[10px] font-bold"
                            >
                              {m.subject}: {m.actualGrade || 'Not taken'} (Needs {m.requiredGrade})
                            </span>
                          ))}
                        </div>
                        <p className="text-[10px] text-rose-700/90 italic pt-0.5">
                          Note: KUCCPS portal automatically rejects applications failing minimum subject thresholds, even if cluster points exceed cutoffs.
                        </p>
                      </div>
                    )}

                    {item.prerequisitesMet && (
                      <p className="text-[10px] text-emerald-800 leading-snug">
                        All mandatory secondary school subject thresholds specified by the university faculties are verified and cleared.
                      </p>
                    )}
                  </div>
                )}

                {/* Match Rationale Preview */}
                <p className="text-[11px] text-slate-600 leading-relaxed line-clamp-2">
                  {item.matchRationale}
                </p>

                {/* Action Buttons: SHAP and Full Details */}
                <div className="pt-2 border-t border-slate-100 grid grid-cols-2 gap-2">
                  <button
                    id={`btn-shap-${item.programmeId}`}
                    onClick={() => onOpenShap(item)}
                    className="py-2 px-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-xl text-[11px] font-bold flex items-center justify-center space-x-1.5 transition-colors cursor-pointer"
                  >
                    <HelpCircle className="w-3.5 h-3.5 text-indigo-500" />
                    <span>Explain Formula (SHAP)</span>
                  </button>

                  <button
                    id={`btn-details-${item.programmeId}`}
                    onClick={() => onOpenDetails(item.programme)}
                    className="py-2 px-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-[11px] font-bold flex items-center justify-center space-x-1 transition-colors cursor-pointer"
                  >
                    <span>Cutoffs & Campuses</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Re-Assessment & Feedback Action Bar */}
      <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div>
          <p className="text-xs font-bold text-slate-900">Are these recommendations accurate?</p>
          <p className="text-[10px] text-slate-500">Submit your evaluation feedback to improve recommendations</p>
        </div>

        <button
          onClick={() => onNavigateToFeedback()}
          className="py-1.5 px-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-[10px] font-bold flex items-center space-x-1 cursor-pointer transition-colors shadow-xs"
        >
          <MessageSquare className="w-3 h-3" />
          <span>Rate & Feedback</span>
        </button>
      </div>
    </div>
  );
};
