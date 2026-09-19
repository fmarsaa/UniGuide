import React, { useState, useEffect, useMemo } from 'react';
import { KCSEGrade, StudentProfile } from '../types';
import { GRADE_POINTS } from '../data/programmes';
import { 
  Save, Sparkles, Check, Plus, X, GraduationCap, Calculator, RefreshCw, 
  LogOut, CheckCircle2, AlertCircle, Trash2, BookOpen, ChevronDown 
} from 'lucide-react';

interface ProfileScreenProps {
  profile: StudentProfile | null;
  onSaveProfile: (profile: StudentProfile) => void;
  onLoadSample: () => void;
  isOnboarding?: boolean;
  onLogout?: () => void;
}

const KCSE_GRADES: KCSEGrade[] = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E'];

interface SubjectMeta {
  name: string;
  category: 'compulsory' | 'science' | 'humanity' | 'applied';
  categoryLabel: string;
}

const ALL_KCSE_SUBJECTS: SubjectMeta[] = [
  // Group 1: Compulsory
  { name: 'English', category: 'compulsory', categoryLabel: 'Compulsory' },
  { name: 'Kiswahili', category: 'compulsory', categoryLabel: 'Compulsory' },
  { name: 'Mathematics', category: 'compulsory', categoryLabel: 'Compulsory' },
  // Group 2: Sciences
  { name: 'Chemistry', category: 'science', categoryLabel: 'Sciences' },
  { name: 'Biology', category: 'science', categoryLabel: 'Sciences' },
  { name: 'Physics', category: 'science', categoryLabel: 'Sciences' },
  // Group 3: Humanities
  { name: 'History', category: 'humanity', categoryLabel: 'Humanities' },
  { name: 'Geography', category: 'humanity', categoryLabel: 'Humanities' },
  { name: 'CRE', category: 'humanity', categoryLabel: 'Humanities' },
  { name: 'IRE', category: 'humanity', categoryLabel: 'Humanities' },
  // Group 4 & 5: Technical & Applied / Languages
  { name: 'Computer Studies', category: 'applied', categoryLabel: 'Technical / Applied' },
  { name: 'Business Studies', category: 'applied', categoryLabel: 'Technical / Applied' },
  { name: 'Agriculture', category: 'applied', categoryLabel: 'Technical / Applied' },
  { name: 'French', category: 'applied', categoryLabel: 'Technical / Applied' },
  { name: 'Home Science', category: 'applied', categoryLabel: 'Technical / Applied' },
  { name: 'Music', category: 'applied', categoryLabel: 'Technical / Applied' },
  { name: 'Art and Design', category: 'applied', categoryLabel: 'Technical / Applied' },
  { name: 'Aviation Technology', category: 'applied', categoryLabel: 'Technical / Applied' },
];

const PRESET_INTERESTS = [
  'Software Development',
  'Artificial Intelligence',
  'Cybersecurity & Networks',
  'Medicine & Clinical Surgery',
  'Dental Medicine & Orthodontics',
  'Nursing & Patient Care',
  'Pharmacy & Drug Development',
  'Physiotherapy & Rehabilitation',
  'Civil & Structural Infrastructure',
  'Geospatial Mapping & GIS',
  'Telecommunications & 5G',
  'Robotics & Industrial Automation',
  'Renewable Energy & Solar PV',
  'Legal Jurisprudence & Justice',
  'Corporate Finance & Auditing',
  'Macroeconomics & Financial Markets',
  'Real Estate & Property Investment',
  'Hospitality & Luxury Tourism',
  'Agribusiness & Food Security',
  'Food Science & Industrial Processing',
  'Biochemistry & Molecular Genetics',
  'Climate Change & Conservation',
  'Journalism & Digital Storytelling',
  'International Relations & Diplomacy',
  'Clinical Psychology & Mental Health',
];

const PRESET_SKILLS = [
  'Problem Solving',
  'Python Coding',
  'Logical Reasoning',
  'Mathematical Analysis',
  'Patient Empathy',
  'Laboratory Diagnostic Testing',
  'Dental Manual Dexterity',
  'Legal Research & Writing',
  'Financial Accounting',
  'CAD & Engineering Drafting',
  'ArcGIS & Spatial Mapping',
  'Optical Fiber Testing',
  'Biomechanical Rehabilitation',
  'Thermodynamics Modeling',
  'Food Quality Auditing (KEBS)',
  'Real Estate Valuation',
  'Multimedia Storytelling',
  'Diplomatic Negotiation',
  'Data Analytics (R/SQL)',
  'System Architecture',
];

const PRESET_STRENGTHS = [
  'Critical Thinking',
  'Analytical Precision',
  'Compassion & Empathy',
  'Advocacy & Public Speaking',
  'Attention to Detail',
  'Strategic Leadership',
  'Perseverance',
  'Curiosity',
  'Cross-Cultural Fluency',
  'Team Collaboration',
];

const PRESET_ASPIRATIONS = [
  'Software Engineer',
  'AI Systems Architect',
  'Medical Doctor (Physician)',
  'Dental Surgeon',
  'High Court Advocate / Legal Counsel',
  'Registered Nurse Specialist',
  'Clinical Pharmacist',
  'Licensed Physiotherapist',
  'Civil Infrastructure Engineer',
  'Geospatial (GIS) Analyst',
  'Telecommunications Engineer',
  'Quantity Surveyor',
  'Renewable Energy Engineer',
  'Robotics & Automation Specialist',
  'Investment Banker / Auditor',
  'Real Estate Asset Valuer',
  'Macroeconomic Policy Analyst',
  'Hotel & Resort Director',
  'Diplomat / Foreign Affairs Envoy',
  'Investigative Journalist',
  'Environmental Sustainability Lead',
  'Agribusiness Value Chain Manager',
  'Food Quality Assurance Manager',
  'Clinical Biochemist',
  'Clinical Psychologist',
];

export const ProfileScreen: React.FC<ProfileScreenProps> = ({
  profile,
  onSaveProfile,
  onLoadSample,
  isOnboarding = false,
  onLogout,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'academic' | 'interests' | 'skills' | 'aspirations'>('academic');

  const [fullName, setFullName] = useState(profile?.fullName || 'Candidate Profile');
  const [indexNumber, setIndexNumber] = useState(profile?.indexNumber || '12345678/2025');
  const [kcseMeanGrade, setKcseMeanGrade] = useState<KCSEGrade>(profile?.kcseMeanGrade || 'A-');

  // Sync with profile if changed externally (e.g. from signup)
  useEffect(() => {
    if (profile?.fullName) setFullName(profile.fullName);
    if (profile?.indexNumber) setIndexNumber(profile.indexNumber);
    if (profile?.kcseMeanGrade) setKcseMeanGrade(profile.kcseMeanGrade);
  }, [profile?.fullName, profile?.indexNumber, profile?.kcseMeanGrade]);
  const [grades, setGrades] = useState<Record<string, KCSEGrade>>(
    profile?.grades || {
      'English': 'A-',
      'Kiswahili': 'B+',
      'Mathematics': 'A',
      'Physics': 'A-',
      'Chemistry': 'B+',
      'Biology': 'B',
      'Computer Studies': 'A',
    }
  );

  const [selectedSubjectToAdd, setSelectedSubjectToAdd] = useState('');

  const [interests, setInterests] = useState<string[]>(
    profile?.interests || ['Software Development', 'Artificial Intelligence', 'Data Science']
  );
  const [skills, setSkills] = useState<string[]>(
    profile?.skills || ['Problem Solving', 'Python Coding', 'Logical Reasoning']
  );
  const [strengths, setStrengths] = useState<string[]>(
    profile?.strengths || ['Critical Thinking', 'Perseverance']
  );
  const [aspirations, setAspirations] = useState<string[]>(
    profile?.aspirations || ['Software Engineer', 'AI Specialist']
  );

  const [customInput, setCustomInput] = useState('');
  const [savedNotice, setSavedNotice] = useState(false);

  // Compute total entered subjects and 7-8 validation
  const subjectCount = Object.keys(grades).length;
  const isSevenToEight = subjectCount >= 7 && subjectCount <= 8;

  // Compute KCSE aggregate points based on best 7 subjects according to KCSE rules:
  // (3 compulsory: Eng, Kis, Math) + (best 2 sciences) + (best 1 humanity) + (best remaining)
  const computedAggregate = useMemo(() => {
    const pts = Object.values(grades).map(g => GRADE_POINTS[g] || 0);
    pts.sort((a, b) => b - a);
    const top7 = pts.slice(0, 7);
    return top7.reduce((acc, curr) => acc + curr, 0);
  }, [grades]);

  // Compute estimated KCSE cluster score
  const estimatedCluster = useMemo(() => {
    const mathPt = GRADE_POINTS[grades['Mathematics'] || 'C'] || 6;
    const engPt = GRADE_POINTS[grades['English'] || 'C'] || 6;
    const sciPt = Math.max(
      GRADE_POINTS[grades['Physics'] || 'E'] || 1,
      GRADE_POINTS[grades['Chemistry'] || 'E'] || 1,
      GRADE_POINTS[grades['Biology'] || 'E'] || 1
    );
    const optPt = Math.max(
      GRADE_POINTS[grades['Computer Studies'] || 'E'] || 1,
      GRADE_POINTS[grades['Business Studies'] || 'E'] || 1,
      GRADE_POINTS[grades['Geography'] || 'E'] || 1,
      GRADE_POINTS[grades['Agriculture'] || 'E'] || 1
    );
    const rawSum = mathPt + engPt + sciPt + (optPt > 1 ? optPt : 6); // max 48
    return Math.min(48, Math.max(15, rawSum * 0.95));
  }, [grades]);

  const handleGradeChange = (subject: string, grade: KCSEGrade) => {
    setGrades(prev => ({ ...prev, [subject]: grade }));
  };

  const handleRemoveSubject = (subjectToRemove: string) => {
    // English and Mathematics are essential for cluster calculations
    if (subjectToRemove === 'English' || subjectToRemove === 'Mathematics') return;
    setGrades(prev => {
      const next = { ...prev };
      delete next[subjectToRemove];
      return next;
    });
  };

  const handleAddSubject = (subjectName: string) => {
    if (!subjectName || grades[subjectName]) return;
    setGrades(prev => ({ ...prev, [subjectName]: 'C+' }));
    setSelectedSubjectToAdd('');
  };

  // Available subjects not yet in student profile
  const availableSubjectsToAdd = useMemo(() => {
    return ALL_KCSE_SUBJECTS.filter(s => !grades[s.name]);
  }, [grades]);

  const toggleItem = (list: string[], setList: React.Dispatch<React.SetStateAction<string[]>>, item: string) => {
    if (list.includes(item)) {
      setList(list.filter(i => i !== item));
    } else {
      setList([...list, item]);
    }
  };

  const addCustomItem = (
    list: string[],
    setList: React.Dispatch<React.SetStateAction<string[]>>
  ) => {
    const trimmed = customInput.trim();
    if (trimmed && !list.includes(trimmed)) {
      setList([...list, trimmed]);
      setCustomInput('');
    }
  };

  const handleSaveAndRecommend = (e: React.FormEvent) => {
    e.preventDefault();
    const updated: StudentProfile = {
      uid: profile?.uid || 'student_' + Date.now(),
      fullName: fullName.trim() || 'Kenyan Form-Four Leaver',
      indexNumber: indexNumber.trim() || '159056/2025',
      kcseMeanGrade,
      kcseMeanPoints: GRADE_POINTS[kcseMeanGrade],
      grades,
      interests,
      skills,
      strengths,
      aspirations,
      calculatedClusterScore: parseFloat(estimatedCluster.toFixed(1)),
      updatedAt: new Date().toISOString(),
    };
    onSaveProfile(updated);
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 2000);
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#F8FAFC] p-4 flex flex-col justify-between space-y-4">
      <div className="space-y-3">
        {/* Onboarding Notice for New Student Signups */}
        {isOnboarding && (
          <div className="bg-gradient-to-r from-teal-500/15 to-indigo-500/15 border-2 border-teal-500/40 rounded-2xl p-3.5 shadow-sm space-y-1.5">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded-full bg-[#0EA5A4] text-white text-[10px] font-black uppercase tracking-wider shadow-xs">
                Step 2 of 2
              </span>
              <span className="text-xs font-black text-indigo-950">
                Welcome, {fullName.split(' ')[0]}! Input Your KCSE Info
              </span>
            </div>
            <p className="text-[11px] text-slate-700 leading-snug">
              Enter your KCSE Mean Grade, subject performance, and career preferences below. Once completed, tap <strong>Save Profile & Generate Top 3 Degrees</strong> to run the Random Forest model.
            </p>
          </div>
        )}

        {/* Top Header & Reset */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
              <GraduationCap className="w-4 h-4 text-[#4F46E5]" />
              <span>Candidate Academic & Career Profile</span>
            </h2>
            <p className="text-[10px] text-slate-500">
              Configure KCSE subjects and career preferences
            </p>
          </div>

          <button
            type="button"
            onClick={onLoadSample}
            className="text-[10px] font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100 flex items-center space-x-1 cursor-pointer"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reset Sample</span>
          </button>
        </div>

        {/* Cluster Points & Aggregate Points Widget */}
        <div className="bg-gradient-to-r from-teal-700 via-indigo-700 to-indigo-900 rounded-xl p-3 text-white shadow-sm flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-white/15 flex items-center justify-center">
              <Calculator className="w-5 h-5 text-teal-200" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <p className="text-[10px] text-teal-100 font-medium">Estimated KUCCPS Cluster</p>
                <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold uppercase tracking-wider ${
                  isSevenToEight ? 'bg-emerald-500/30 text-emerald-200 border border-emerald-400/30' : 'bg-amber-400/30 text-amber-200 border border-amber-300/30'
                }`}>
                  {subjectCount} / 7–8 Subjects
                </span>
              </div>
              <p className="text-xs text-slate-200 font-semibold">
                Best 7 Aggregate: <span className="font-mono text-amber-200 font-bold">{computedAggregate} / 84 pts</span>
              </p>
            </div>
          </div>
          <div className="text-right">
            <span className="text-lg font-black tracking-tight">{estimatedCluster.toFixed(1)}</span>
            <span className="text-[10px] text-teal-200 ml-0.5">/ 48</span>
          </div>
        </div>

        {/* Segmented SubTabs */}
        <div className="flex rounded-xl bg-slate-200/80 p-1 text-[11px] font-semibold">
          <button
            type="button"
            onClick={() => setActiveSubTab('academic')}
            className={`flex-1 py-1.5 rounded-lg transition-all text-center ${
              activeSubTab === 'academic' ? 'bg-white text-[#14213D] shadow-xs' : 'text-slate-600'
            }`}
          >
            Grades
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('interests')}
            className={`flex-1 py-1.5 rounded-lg transition-all text-center ${
              activeSubTab === 'interests' ? 'bg-white text-[#14213D] shadow-xs' : 'text-slate-600'
            }`}
          >
            Interests ({interests.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('skills')}
            className={`flex-1 py-1.5 rounded-lg transition-all text-center ${
              activeSubTab === 'skills' ? 'bg-white text-[#14213D] shadow-xs' : 'text-slate-600'
            }`}
          >
            Skills
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('aspirations')}
            className={`flex-1 py-1.5 rounded-lg transition-all text-center ${
              activeSubTab === 'aspirations' ? 'bg-white text-[#14213D] shadow-xs' : 'text-slate-600'
            }`}
          >
            Aspirations
          </button>
        </div>

        {/* Tab 1: Academic Grades */}
        {activeSubTab === 'academic' && (
          <div className="space-y-3">
            {/* Student ID & Name */}
            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] font-bold text-slate-600">Candidate Name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full mt-0.5 px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg font-medium"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-slate-600">Index Number</label>
                  <input
                    type="text"
                    value={indexNumber}
                    onChange={(e) => setIndexNumber(e.target.value)}
                    className="w-full mt-0.5 px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg font-medium"
                  />
                </div>
              </div>

              {/* KCSE Mean Grade Selector */}
              <div>
                <label className="text-[10px] font-bold text-slate-700 block mb-1">
                  KCSE Overall Mean Grade (Points: {GRADE_POINTS[kcseMeanGrade]}/12)
                </label>
                <div className="grid grid-cols-6 gap-1">
                  {KCSE_GRADES.slice(0, 6).map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setKcseMeanGrade(g)}
                      className={`py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                        kcseMeanGrade === g
                          ? 'bg-[#4F46E5] text-white shadow-xs scale-102'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
                <div className="grid grid-cols-6 gap-1 mt-1">
                  {KCSE_GRADES.slice(6, 12).map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setKcseMeanGrade(g)}
                      className={`py-1 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                        kcseMeanGrade === g
                          ? 'bg-[#4F46E5] text-white shadow-xs scale-102'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* 7-8 Subject Entry & Verification Breakdown */}
            <div className="bg-white rounded-xl p-3.5 border border-slate-200/80 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-[#4F46E5]" />
                    <span>KCSE Subject Breakdown ({subjectCount} Entered)</span>
                  </h3>
                  <p className="text-[10px] text-slate-500">
                    Form-Four certificates require exactly 7 or 8 subjects for KUCCPS admission
                  </p>
                </div>

                <div className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center space-x-1 ${
                  isSevenToEight ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-200'
                }`}>
                  {isSevenToEight ? (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      <span>Valid (7-8)</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-3 h-3 text-amber-600" />
                      <span>{subjectCount < 7 ? `Add ${7 - subjectCount} more` : 'Max 8 subjects'}</span>
                    </>
                  )}
                </div>
              </div>

              {/* 7-8 Subject Guidance Callout */}
              {!isSevenToEight && (
                <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-300 text-[11px] text-amber-900 flex items-start space-x-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <p className="leading-tight">
                    {subjectCount < 7
                      ? `Kenya National Examinations Council (KNEC) grades candidates on 7 or 8 subjects. You have entered ${subjectCount}. Add at least ${7 - subjectCount} more below.`
                      : `You have entered ${subjectCount} subjects. KUCCPS evaluates candidates on a maximum of 8 KCSE subjects. Remove extra subjects to match your official certificate.`}
                  </p>
                </div>
              )}

              {/* Subject Entries List */}
              <div className="space-y-1.5 pt-1">
                {Object.entries(grades).map(([subject, currentGrade]) => {
                  const meta = ALL_KCSE_SUBJECTS.find(s => s.name === subject);
                  const isCompulsory = meta?.category === 'compulsory' || subject === 'English' || subject === 'Mathematics';

                  return (
                    <div
                      key={subject}
                      className="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-slate-50 hover:bg-slate-100/80 border border-slate-200/70 transition-colors"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold text-slate-800">{subject}</span>
                        {meta && (
                          <span className={`text-[9px] px-1.5 py-0.2 rounded-md font-bold uppercase tracking-wider ${
                            meta.category === 'compulsory'
                              ? 'bg-blue-100 text-blue-800'
                              : meta.category === 'science'
                              ? 'bg-emerald-100 text-emerald-800'
                              : meta.category === 'humanity'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-purple-100 text-purple-800'
                          }`}>
                            {meta.categoryLabel}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center space-x-1.5">
                        <select
                          value={currentGrade}
                          onChange={(e) => handleGradeChange(subject, e.target.value as KCSEGrade)}
                          className="text-xs font-black bg-white px-2 py-1 border border-slate-300 rounded-md text-[#4F46E5] focus:outline-none focus:ring-1 focus:ring-indigo-400"
                        >
                          {KCSE_GRADES.map((g) => (
                            <option key={g} value={g}>
                              {g} ({GRADE_POINTS[g]} pts)
                            </option>
                          ))}
                        </select>

                        {!isCompulsory && (
                          <button
                            type="button"
                            title={`Remove ${subject}`}
                            onClick={() => handleRemoveSubject(subject)}
                            className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded cursor-pointer transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Add Subject Section */}
              {availableSubjectsToAdd.length > 0 && subjectCount < 9 && (
                <div className="pt-2 border-t border-slate-100 flex items-center space-x-2">
                  <select
                    value={selectedSubjectToAdd}
                    onChange={(e) => setSelectedSubjectToAdd(e.target.value)}
                    className="flex-1 text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 focus:outline-none"
                  >
                    <option value="">+ Add another KCSE subject (Sciences, Humanities, Technical)...</option>
                    {availableSubjectsToAdd.map((s) => (
                      <option key={s.name} value={s.name}>
                        {s.name} ({s.categoryLabel})
                      </option>
                    ))}
                  </select>

                  <button
                    type="button"
                    disabled={!selectedSubjectToAdd}
                    onClick={() => handleAddSubject(selectedSubjectToAdd)}
                    className="px-3 py-1.5 bg-[#4F46E5] disabled:bg-slate-200 text-white disabled:text-slate-400 text-xs font-bold rounded-lg flex items-center space-x-1 cursor-pointer disabled:cursor-not-allowed transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: Interests */}
        {activeSubTab === 'interests' && (
          <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs space-y-3">
            <div>
              <h3 className="text-xs font-bold text-slate-900">Academic & Career Interests</h3>
              <p className="text-[10px] text-slate-500">Tap to select your passions</p>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {PRESET_INTERESTS.map((item) => {
                const isSelected = interests.includes(item);
                return (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleItem(interests, setInterests, item)}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all flex items-center space-x-1 cursor-pointer ${
                      isSelected
                        ? 'bg-[#4F46E5] text-white shadow-xs'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3" />}
                    <span>{item}</span>
                  </button>
                );
              })}
            </div>

            {/* Custom Input */}
            <div className="pt-2 border-t border-slate-100 flex items-center space-x-1.5">
              <input
                type="text"
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                placeholder="Add custom interest..."
                className="flex-1 px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg"
              />
              <button
                type="button"
                onClick={() => addCustomItem(interests, setInterests)}
                className="px-3 py-1.5 bg-slate-800 text-white rounded-lg text-xs font-bold flex items-center space-x-1"
              >
                <Plus className="w-3 h-3" />
                <span>Add</span>
              </button>
            </div>
          </div>
        )}

        {/* Tab 3: Skills & Strengths */}
        {activeSubTab === 'skills' && (
          <div className="space-y-3">
            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs space-y-2">
              <h3 className="text-xs font-bold text-slate-900">Technical & Cognitive Skills</h3>
              <div className="flex flex-wrap gap-1.5">
                {PRESET_SKILLS.map((item) => {
                  const isSelected = skills.includes(item);
                  return (
                    <button
                      key={item}
                      type="button"
                      onClick={() => toggleItem(skills, setSkills, item)}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all flex items-center space-x-1 cursor-pointer ${
                        isSelected
                          ? 'bg-[#0EA5A4] text-white shadow-xs'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {isSelected && <Check className="w-3 h-3" />}
                      <span>{item}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs space-y-2">
              <h3 className="text-xs font-bold text-slate-900">Personal Strengths</h3>
              <div className="flex flex-wrap gap-1.5">
                {PRESET_STRENGTHS.map((item) => {
                  const isSelected = strengths.includes(item);
                  return (
                    <button
                      key={item}
                      type="button"
                      onClick={() => toggleItem(strengths, setStrengths, item)}
                      className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all flex items-center space-x-1 cursor-pointer ${
                        isSelected
                          ? 'bg-indigo-600 text-white shadow-xs'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {isSelected && <Check className="w-3 h-3" />}
                      <span>{item}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Aspirations */}
        {activeSubTab === 'aspirations' && (
          <div className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs space-y-3">
            <div>
              <h3 className="text-xs font-bold text-slate-900">Long-term Career Aspirations</h3>
              <p className="text-[10px] text-slate-500">Target professions after university graduation</p>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {PRESET_ASPIRATIONS.map((item) => {
                const isSelected = aspirations.includes(item);
                return (
                  <button
                    key={item}
                    type="button"
                    onClick={() => toggleItem(aspirations, setAspirations, item)}
                    className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all flex items-center space-x-1 cursor-pointer ${
                      isSelected
                        ? 'bg-amber-600 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3" />}
                    <span>{item}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Floating Bottom Action */}
      <div className="pt-2 sticky bottom-0 bg-[#F8FAFC]/90 backdrop-blur-xs space-y-2">
        <button
          type="button"
          onClick={handleSaveAndRecommend}
          className="w-full py-3 bg-gradient-to-r from-[#0EA5A4] to-[#4F46E5] hover:opacity-95 text-white rounded-xl text-xs font-black shadow-lg shadow-indigo-500/20 flex items-center justify-center space-x-2 active:scale-98 cursor-pointer transition-all"
        >
          <Sparkles className="w-4 h-4 text-teal-200 animate-pulse" />
          <span>Save Profile & Generate Top 3 Degrees</span>
        </button>

        {onLogout && (
          <button
            type="button"
            onClick={onLogout}
            className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 cursor-pointer transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Log Out of Student Account</span>
          </button>
        )}
      </div>
    </div>
  );
};
