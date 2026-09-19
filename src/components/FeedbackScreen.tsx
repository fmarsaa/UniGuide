import React, { useState } from 'react';
import { ProgrammeInfo, FeedbackEntry } from '../types';
import { Star, MessageSquare, Check, ArrowRight, RotateCcw, ThumbsUp, Send } from 'lucide-react';

interface FeedbackScreenProps {
  programmes: ProgrammeInfo[];
  feedbacks: FeedbackEntry[];
  initialProgrammeId?: string;
  onSubmitFeedback: (entry: Omit<FeedbackEntry, 'id' | 'timestamp'>) => void;
  onNavigateToProfile: () => void;
}

export const FeedbackScreen: React.FC<FeedbackScreenProps> = ({
  programmes,
  feedbacks,
  initialProgrammeId,
  onSubmitFeedback,
  onNavigateToProfile,
}) => {
  const [selectedProgId, setSelectedProgId] = useState<string>(
    initialProgrammeId || programmes[0]?.id || 'prog_01'
  );
  const [rating, setRating] = useState<number>(5);
  const [satisfactionScore, setSatisfactionScore] = useState<number>(9);
  const [plannedProgramme, setPlannedProgramme] = useState('');
  const [comments, setComments] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const prog = programmes.find((p) => p.id === selectedProgId);

    onSubmitFeedback({
      uid: 'user_active',
      programmeId: selectedProgId,
      programmeName: prog ? prog.name : 'University Programme',
      rating,
      satisfactionScore,
      plannedProgramme: plannedProgramme.trim() || undefined,
      comments: comments.trim() || 'Recommendations aligned with my career objectives.',
    });

    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      setComments('');
      setPlannedProgramme('');
    }, 2500);
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#F8FAFC] p-4 space-y-4">
      {/* Header */}
      <div>
        <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
          <MessageSquare className="w-4 h-4 text-[#4F46E5]" />
          <span>Recommendation Evaluation (Wireframe 4.11)</span>
        </h2>
        <p className="text-[10px] text-slate-500">
          Your feedback evaluates the Random Forest model and improves decision support accuracy
        </p>
      </div>

      {/* Main Feedback Form Card */}
      <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-xs space-y-3">
        {submitted ? (
          <div className="py-6 text-center space-y-2">
            <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
              <Check className="w-6 h-6" />
            </div>
            <h3 className="text-xs font-bold text-slate-900">Feedback Submitted Successfully!</h3>
            <p className="text-[10px] text-slate-500 max-w-xs mx-auto">
              As described in the study methodology, your response is stored in Firestore for model usability and relevance evaluation.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3 text-xs">
            {/* Programme Selector */}
            <div>
              <label className="text-[10px] font-bold text-slate-700 block mb-1">
                Select Recommended Programme to Rate
              </label>
              <select
                value={selectedProgId}
                onChange={(e) => setSelectedProgId(e.target.value)}
                className="w-full px-2.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl font-medium focus:outline-none focus:ring-2 focus:ring-[#4F46E5]"
              >
                {programmes.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.code})
                  </option>
                ))}
              </select>
            </div>

            {/* 5-Star Rating */}
            <div>
              <label className="text-[10px] font-bold text-slate-700 block mb-1">
                Recommendation Relevance Rating
              </label>
              <div className="flex items-center space-x-2 bg-slate-50 p-2 rounded-xl border border-slate-100">
                <div className="flex items-center space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className="p-1 text-slate-300 hover:text-amber-400 focus:outline-none transition-colors cursor-pointer"
                    >
                      <Star
                        className={`w-6 h-6 ${
                          star <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-300'
                        }`}
                      />
                    </button>
                  ))}
                </div>
                <span className="text-[11px] font-extrabold text-slate-700 ml-2">
                  {rating === 5
                    ? 'Excellent Match'
                    : rating === 4
                    ? 'Good Match'
                    : rating === 3
                    ? 'Moderate'
                    : 'Unsuitable'}
                </span>
              </div>
            </div>

            {/* Satisfaction Slider (1-10) */}
            <div>
              <div className="flex justify-between text-[10px] font-bold text-slate-700 mb-1">
                <span>Model Transparency & Explanation Satisfaction</span>
                <span className="text-[#4F46E5] font-black">{satisfactionScore} / 10</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={satisfactionScore}
                onChange={(e) => setSatisfactionScore(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#4F46E5]"
              />
              <div className="flex justify-between text-[9px] text-slate-400 mt-0.5">
                <span>1 (Confusing)</span>
                <span>10 (Very Transparent)</span>
              </div>
            </div>

            {/* Actually Planned Programme */}
            <div>
              <label className="text-[10px] font-bold text-slate-700 block mb-1">
                What university degree do you currently plan to apply for? (Optional)
              </label>
              <input
                type="text"
                value={plannedProgramme}
                onChange={(e) => setPlannedProgramme(e.target.value)}
                placeholder="e.g. Informatics and Computer Science"
                className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg"
              />
            </div>

            {/* Comments */}
            <div>
              <label className="text-[10px] font-bold text-slate-700 block mb-1">
                Student Feedback & Comments
              </label>
              <textarea
                rows={2}
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="How did the SHAP explanations help you understand the match?"
                className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#4F46E5]"
              />
            </div>

            <button
              type="submit"
              className="w-full py-2.5 bg-[#4F46E5] hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md flex items-center justify-center space-x-1.5 cursor-pointer active:scale-98"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit Model Evaluation</span>
            </button>
          </form>
        )}
      </div>

      {/* Profile Adjustment Option (Figure 4.2: Option B) */}
      <div className="bg-indigo-50 rounded-xl p-3.5 border border-indigo-100 flex items-center justify-between">
        <div>
          <h4 className="text-xs font-bold text-indigo-900">Want different recommendations?</h4>
          <p className="text-[10px] text-indigo-700">
            Revise your KCSE subject grades, skills, or career aspirations
          </p>
        </div>

        <button
          onClick={onNavigateToProfile}
          className="px-3 py-1.5 bg-white text-indigo-700 border border-indigo-200 hover:bg-indigo-50 rounded-lg text-[10px] font-bold flex items-center space-x-1 cursor-pointer transition-colors shadow-2xs"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Adjust Profile</span>
        </button>
      </div>

      {/* Recent Feedback Feed */}
      <div className="space-y-2">
        <h4 className="text-xs font-bold text-slate-800">Recent Student Evaluations</h4>
        <div className="space-y-2">
          {feedbacks.slice(0, 3).map((fb) => (
            <div
              key={fb.id}
              className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs space-y-1"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-800 truncate max-w-[200px]">
                  {fb.programmeName}
                </span>
                <div className="flex items-center space-x-0.5">
                  {Array.from({ length: fb.rating }).map((_, i) => (
                    <Star key={i} className="w-3 h-3 text-amber-400 fill-amber-400" />
                  ))}
                </div>
              </div>
              <p className="text-[11px] text-slate-600 italic leading-snug">
                &ldquo;{fb.comments}&rdquo;
              </p>
              <span className="text-[9px] text-slate-400 block font-mono">{fb.timestamp}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
