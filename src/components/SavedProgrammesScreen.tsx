import React from 'react';
import { ProgrammeInfo } from '../types';
import { Bookmark, Trash2, ChevronRight, Sparkles, Building2, BookOpen } from 'lucide-react';

interface SavedProgrammesScreenProps {
  savedProgrammes: ProgrammeInfo[];
  onRemoveSave: (id: string) => void;
  onOpenDetails: (programme: ProgrammeInfo) => void;
  onNavigateToRecommendations: () => void;
}

export const SavedProgrammesScreen: React.FC<SavedProgrammesScreenProps> = ({
  savedProgrammes,
  onRemoveSave,
  onOpenDetails,
  onNavigateToRecommendations,
}) => {
  if (savedProgrammes.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-4 bg-[#F8FAFC]">
        <div className="w-16 h-16 rounded-2xl bg-amber-50 text-amber-500 flex items-center justify-center shadow-inner">
          <Bookmark className="w-8 h-8" />
        </div>
        <div>
          <h2 className="text-base font-bold text-slate-900">Your Shortlist is Empty</h2>
          <p className="text-xs text-slate-500 max-w-xs mx-auto mt-1 leading-relaxed">
            Bookmark university programmes you are interested in applying for through KUCCPS to compare their requirements here.
          </p>
        </div>
        <button
          onClick={onNavigateToRecommendations}
          className="py-2.5 px-5 bg-[#4F46E5] text-white rounded-xl text-xs font-bold shadow-md hover:bg-indigo-700 transition-all cursor-pointer"
        >
          View Recommended Degrees
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-[#F8FAFC] p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
            <Bookmark className="w-4 h-4 text-amber-500 fill-amber-500" />
            <span>Shortlisted Degree Programmes</span>
          </h2>
          <p className="text-[10px] text-slate-500">
            {savedProgrammes.length} programmes saved for final KUCCPS submission
          </p>
        </div>

        <button
          onClick={onNavigateToRecommendations}
          className="text-[10px] font-bold text-[#4F46E5] bg-indigo-50 px-2 py-1 rounded-lg hover:bg-indigo-100 flex items-center space-x-1"
        >
          <Sparkles className="w-3 h-3 text-indigo-500" />
          <span>Top 3 AI</span>
        </button>
      </div>

      <div className="space-y-2">
        {savedProgrammes.map((prog) => {
          const primaryUni = prog.universities[0];

          return (
            <div
              key={prog.id}
              className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-0.5 flex-1 min-w-0">
                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700">
                    {prog.code}
                  </span>
                  <h3 className="text-xs font-bold text-slate-900 leading-snug truncate">
                    {prog.name}
                  </h3>
                  <p className="text-[10px] text-slate-500 truncate">
                    {prog.faculty}
                  </p>
                </div>

                <button
                  onClick={() => onRemoveSave(prog.id)}
                  className="p-1.5 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                  title="Remove from saved"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px]">
                <span className="text-slate-600">
                  Cutoff: <strong className="text-slate-800">{primaryUni?.lastCutoffPoints || 38.5} pts</strong> ({primaryUni?.name})
                </span>

                <button
                  onClick={() => onOpenDetails(prog)}
                  className="font-bold text-[#4F46E5] hover:underline flex items-center space-x-0.5 cursor-pointer"
                >
                  <span>View Details</span>
                  <ChevronRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
