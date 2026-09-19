import React, { useState, useMemo } from 'react';
import { ProgrammeInfo, StudentProfile } from '../types';
import { GRADE_POINTS } from '../data/programmes';
import { 
  X, Bookmark, BookmarkCheck, Building2, BookOpen, Briefcase, 
  Award, CheckCircle2, ChevronRight, ExternalLink, ShieldAlert, 
  ShieldCheck, AlertCircle 
} from 'lucide-react';

interface ProgrammeDetailsModalProps {
  programme: ProgrammeInfo;
  isSaved: boolean;
  studentProfile?: StudentProfile | null;
  onToggleSave: (id: string) => void;
  onClose: () => void;
}

export const ProgrammeDetailsModal: React.FC<ProgrammeDetailsModalProps> = ({
  programme,
  isSaved,
  studentProfile,
  onToggleSave,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'universities' | 'careers' | 'certifications'>('overview');

  // Verify prerequisites against student profile if available
  const prereqValidation = useMemo(() => {
    if (!studentProfile || !studentProfile.grades) return null;
    const required = programme.admissionRequirements.requiredSubjects;
    const missing: { subject: string; requiredGrade: string; actualGrade?: string }[] = [];
    const satisfied: { subject: string; grade: string }[] = [];

    for (const req of required) {
      const studentGrade = studentProfile.grades[req.subject];
      const reqPoints = GRADE_POINTS[req.minGrade] || 0;
      const studentPoints = studentGrade ? (GRADE_POINTS[studentGrade] || 0) : 0;

      if (!studentGrade || studentPoints < reqPoints) {
        missing.push({
          subject: req.subject,
          requiredGrade: req.minGrade,
          actualGrade: studentGrade,
        });
      } else {
        satisfied.push({
          subject: req.subject,
          grade: studentGrade,
        });
      }
    }

    const meanMet = (GRADE_POINTS[studentProfile.kcseMeanGrade] || 0) >= programme.admissionRequirements.minimumMeanPoints;

    return {
      allMet: missing.length === 0 && meanMet,
      meanMet,
      missing,
      satisfied,
    };
  }, [programme, studentProfile]);

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      {/* Mobile Bottom Sheet Container */}
      <div className="bg-white w-full max-w-md rounded-t-[32px] sm:rounded-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden border border-slate-200 animate-in slide-in-from-bottom duration-300">
        {/* Drag Handle */}
        <div className="pt-3 pb-1 flex justify-center sm:hidden">
          <div className="w-12 h-1.5 bg-slate-300 rounded-full" />
        </div>

        {/* Modal Header */}
        <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between shrink-0 bg-slate-50/70">
          <div className="flex-1 pr-2">
            <span className="text-[10px] font-bold text-[#4F46E5] uppercase tracking-wider">
              {programme.category} &bull; {programme.code}
            </span>
            <h3 className="text-xs font-black text-slate-900 leading-tight">
              {programme.name}
            </h3>
          </div>

          <div className="flex items-center space-x-1.5 shrink-0">
            <button
              onClick={() => onToggleSave(programme.id)}
              className={`p-1.5 rounded-lg transition-colors ${
                isSaved ? 'text-amber-500 bg-amber-50' : 'text-slate-400 hover:text-slate-600'
              }`}
              title={isSaved ? 'Remove from Saved' : 'Save Programme'}
            >
              {isSaved ? <BookmarkCheck className="w-4 h-4 fill-amber-500" /> : <Bookmark className="w-4 h-4" />}
            </button>

            <button
              onClick={onClose}
              className="w-7 h-7 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Mobile Tabs */}
        <div className="flex border-b border-slate-200 bg-white px-3 text-[11px] font-bold text-slate-500">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-3 border-b-2 transition-all ${
              activeTab === 'overview' ? 'border-[#4F46E5] text-[#4F46E5]' : 'border-transparent'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('universities')}
            className={`py-2 px-3 border-b-2 transition-all ${
              activeTab === 'universities' ? 'border-[#4F46E5] text-[#4F46E5]' : 'border-transparent'
            }`}
          >
            Universities ({programme.universities.length})
          </button>
          <button
            onClick={() => setActiveTab('careers')}
            className={`py-2 px-3 border-b-2 transition-all ${
              activeTab === 'careers' ? 'border-[#4F46E5] text-[#4F46E5]' : 'border-transparent'
            }`}
          >
            Careers
          </button>
          <button
            onClick={() => setActiveTab('certifications')}
            className={`py-2 px-3 border-b-2 transition-all ${
              activeTab === 'certifications' ? 'border-[#4F46E5] text-[#4F46E5]' : 'border-transparent'
            }`}
          >
            Certifications
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs">
          {/* 1. Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-3.5">
              <div>
                <h4 className="text-xs font-bold text-slate-900 mb-1">Programme Summary</h4>
                <p className="text-slate-600 text-[11px] leading-relaxed">
                  {programme.overview}
                </p>
              </div>

              {/* Candidate Subject Prerequisite Clearance Status (Prominent Disclaimer) */}
              {prereqValidation && (
                <div className={`p-3 rounded-xl border text-[11px] space-y-2 ${
                  prereqValidation.allMet
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                    : 'bg-rose-50 border-rose-300 text-rose-950'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1.5 font-bold text-xs">
                      {prereqValidation.allMet ? (
                        <>
                          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                          <span className="text-emerald-900">Official Prerequisites Cleared</span>
                        </>
                      ) : (
                        <>
                          <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
                          <span className="text-rose-900">Prerequisite Shortfall Alert</span>
                        </>
                      )}
                    </div>

                    <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                      prereqValidation.allMet
                        ? 'bg-emerald-600 text-white'
                        : 'bg-rose-600 text-white'
                    }`}>
                      {prereqValidation.allMet ? 'Verified Eligible' : 'Ineligible on Subjects'}
                    </span>
                  </div>

                  {!prereqValidation.allMet && prereqValidation.missing.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-[10px] text-rose-800 font-semibold">
                        You do not meet minimum subject grade thresholds:
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                        {prereqValidation.missing.map((m, idx) => (
                          <div
                            key={idx}
                            className="bg-white/90 p-1.5 rounded-lg border border-rose-200 text-[10px] flex items-center justify-between"
                          >
                            <span className="font-semibold text-rose-900">{m.subject}</span>
                            <span className="font-mono text-rose-700 font-bold">
                              Your: {m.actualGrade || 'Missing'} (Min: {m.requiredGrade})
                            </span>
                          </div>
                        ))}
                      </div>
                      <p className="text-[10px] text-rose-700/90 italic pt-1">
                        KUCCPS system rules enforce that even candidates who meet the cutoff points are disqualified if any prerequisite subject threshold is unmet.
                      </p>
                    </div>
                  )}

                  {prereqValidation.allMet && (
                    <p className="text-[10px] text-emerald-800 leading-snug">
                      Your KCSE performance satisfies both the minimum mean grade and all specific subject requirements for this degree programme.
                    </p>
                  )}
                </div>
              )}

              {/* Admission Criteria Card */}
              <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200/80 space-y-2">
                <h4 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-[#4F46E5]" />
                  <span>KUCCPS Admission Requirements</span>
                </h4>

                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Minimum KCSE Mean</span>
                    <strong className="text-slate-800 text-xs">
                      Grade {programme.admissionRequirements.minimumMeanGrade} ({programme.admissionRequirements.minimumMeanPoints} pts)
                    </strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Programme Duration</span>
                    <strong className="text-slate-800 text-xs">
                      {programme.durationYears} Academic Years
                    </strong>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-200/70 space-y-1">
                  <span className="text-[10px] font-bold text-slate-600">Essential Subject Minimums:</span>
                  <div className="grid grid-cols-2 gap-1">
                    {programme.admissionRequirements.requiredSubjects.map((req) => {
                      const studentGrade = studentProfile?.grades?.[req.subject];
                      const isSatisfied = studentGrade && (GRADE_POINTS[studentGrade] || 0) >= (GRADE_POINTS[req.minGrade] || 0);

                      return (
                        <div
                          key={req.subject}
                          className={`flex items-center justify-between p-1.5 rounded border text-[10px] ${
                            studentGrade
                              ? isSatisfied
                                ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
                                : 'bg-rose-50/70 border-rose-200 text-rose-900'
                              : 'bg-white border-slate-100 text-slate-700'
                          }`}
                        >
                          <div className="flex items-center space-x-1 truncate">
                            {studentGrade ? (
                              isSatisfied ? (
                                <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
                              ) : (
                                <AlertCircle className="w-3 h-3 text-rose-600 shrink-0" />
                              )
                            ) : (
                              <CheckCircle2 className="w-3 h-3 text-slate-400 shrink-0" />
                            )}
                            <span className="truncate">{req.subject}: <strong>{req.minGrade}</strong></span>
                          </div>
                          {studentGrade && (
                            <span className="font-mono text-[9px] font-bold ml-1">
                              (You: {studentGrade})
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                <p className="text-[10px] text-slate-500 italic pt-1">
                  Cluster Group: {programme.admissionRequirements.clusterSubjectGroup}
                </p>
              </div>
            </div>
          )}

          {/* 2. Universities Tab */}
          {activeTab === 'universities' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-900">
                Accredited Universities in Kenya Offering this Degree
              </h4>

              <div className="space-y-2">
                {programme.universities.map((uni) => (
                  <div
                    key={uni.name}
                    className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 flex items-start justify-between gap-2"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center space-x-1.5">
                        <span className="font-bold text-xs text-slate-900">{uni.name}</span>
                      </div>
                      <p className="text-[10px] text-slate-500">
                        Location: {uni.location} &bull; <span className="font-semibold">{uni.type}</span>
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[9px] text-slate-400 block">Cutoff</span>
                      <span className="text-xs font-black text-[#4F46E5]">
                        {uni.lastCutoffPoints} pts
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Career Pathways Tab */}
          {activeTab === 'careers' && (
            <div className="space-y-3">
              <div>
                <h4 className="text-xs font-bold text-slate-900 mb-1 flex items-center space-x-1">
                  <Briefcase className="w-3.5 h-3.5 text-[#4F46E5]" />
                  <span>Target Professional Career Pathways</span>
                </h4>
                <p className="text-[10px] text-slate-500">
                  Common roles entered by Kenyan and international graduates
                </p>
              </div>

              <div className="space-y-1.5">
                {programme.careerPathways.map((career, i) => (
                  <div
                    key={i}
                    className="p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-slate-800 text-[11px] font-semibold flex items-center space-x-2"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-[#0EA5A4]" />
                    <span>{career}</span>
                  </div>
                ))}
              </div>

              <div className="pt-2">
                <h5 className="text-[11px] font-bold text-slate-800 mb-1.5">In-Demand Technical & Soft Skills</h5>
                <div className="flex flex-wrap gap-1.5">
                  {programme.recommendedSkills.map((skill, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[10px] font-medium border border-indigo-100"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 4. Certifications Tab */}
          {activeTab === 'certifications' && (
            <div className="space-y-3">
              <div>
                <h4 className="text-xs font-bold text-slate-900 mb-1 flex items-center space-x-1">
                  <Award className="w-3.5 h-3.5 text-amber-500" />
                  <span>Recommended Industry Certifications</span>
                </h4>
                <p className="text-[10px] text-slate-500">
                  Certifications that boost employability during or after studies
                </p>
              </div>

              <div className="space-y-2">
                {programme.certifications.map((cert, i) => (
                  <div
                    key={i}
                    className="p-2.5 bg-amber-50/60 rounded-xl border border-amber-200/60 flex items-start space-x-2 text-amber-900"
                  >
                    <Award className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-xs font-bold block">{cert}</span>
                      <span className="text-[10px] text-amber-700">Recognized globally & locally in Kenya</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="p-3.5 border-t border-slate-100 bg-slate-50 shrink-0 flex items-center space-x-2">
          <button
            onClick={() => onToggleSave(programme.id)}
            className={`flex-1 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center space-x-1.5 transition-colors cursor-pointer ${
              isSaved
                ? 'bg-amber-100 text-amber-900 hover:bg-amber-200'
                : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-100'
            }`}
          >
            {isSaved ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
            <span>{isSaved ? 'Saved to Shortlist' : 'Add to Shortlist'}</span>
          </button>

          <button
            onClick={onClose}
            className="flex-1 py-2.5 bg-[#4F46E5] hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};
