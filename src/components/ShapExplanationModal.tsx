import React from 'react';
import { RecommendationResult } from '../types';
import { X, CheckCircle, TrendingUp, AlertTriangle, Sparkles, Award, Calculator, School } from 'lucide-react';

interface ShapExplanationModalProps {
  result: RecommendationResult;
  onClose: () => void;
}

export const ShapExplanationModal: React.FC<ShapExplanationModalProps> = ({
  result,
  onClose,
}) => {
  const { shapExplanation, programme } = result;
  const features = Object.entries(shapExplanation.featureImportances).sort((a, b) => b[1] - a[1]);

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200">
      {/* Mobile Bottom Sheet Container */}
      <div className="bg-white w-full max-w-md rounded-t-[32px] sm:rounded-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden border border-slate-200 animate-in slide-in-from-bottom duration-300">
        {/* Mobile Drag Handle */}
        <div className="pt-3 pb-1 flex justify-center sm:hidden">
          <div className="w-12 h-1.5 bg-slate-300 rounded-full" />
        </div>

        {/* Modal Header */}
        <div className="px-5 py-3.5 border-b border-slate-100 flex items-center justify-between shrink-0 bg-slate-50/50">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-[#4F46E5] flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-black text-slate-900 leading-tight">
                Explainability & KUCCPS Metrics
              </h3>
              <p className="text-[10px] text-slate-500 line-clamp-1">
                {programme.name}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-7 h-7 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs">
          {/* Official KUCCPS Mathematical Calculation Card */}
          <div className="bg-slate-900 text-white rounded-xl p-3.5 space-y-2.5 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5 text-amber-400 font-bold text-xs">
                <Calculator className="w-4 h-4" />
                <span>KUCCPS Cluster Weighted Points (CWP)</span>
              </div>
              <span className="text-[10px] font-mono bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                Formula: C = √((r/48) × (t/84)) × 48
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 bg-slate-800/80 rounded-lg p-2.5 text-center text-[11px]">
              <div>
                <span className="text-[9px] text-slate-400 block">Raw 4 Subjects (r)</span>
                <span className="font-mono font-bold text-white text-xs">
                  {result.rawClusterTotal || 44} / 48
                </span>
              </div>
              <div>
                <span className="text-[9px] text-slate-400 block">Aggregate 7 (t)</span>
                <span className="font-mono font-bold text-white text-xs">
                  {result.aggregatePoints || 76} / 84
                </span>
              </div>
              <div>
                <span className="text-[9px] text-amber-400 block">Calculated CWP (C)</span>
                <span className="font-mono font-black text-amber-300 text-sm">
                  {result.calculatedClusterScore ? result.calculatedClusterScore.toFixed(3) : '41.800'}
                </span>
              </div>
            </div>

            {/* Subject cluster inputs */}
            {result.clusterSubjectBreakdown && result.clusterSubjectBreakdown.length > 0 && (
              <div className="space-y-1 text-[10px] text-slate-300 pt-1 border-t border-slate-800">
                <span className="text-slate-400 font-semibold block">Cluster Subjects Selected:</span>
                <div className="grid grid-cols-2 gap-1.5 font-mono">
                  {result.clusterSubjectBreakdown.map((item, idx) => (
                    <div key={idx} className="bg-slate-800 px-2 py-1 rounded flex justify-between">
                      <span className="truncate">{item.subject}</span>
                      <span className="text-amber-400 font-bold ml-1">{item.grade} ({item.points} pts)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="text-[10px] text-slate-300 flex items-center justify-between pt-1">
              <span>Benchmark Cutoff: <strong className="text-white">{result.targetCutoff || 38.5} pts</strong></span>
              <span className={`font-bold ${result.cutoffDifference >= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {result.cutoffDifference >= 0
                  ? `+${result.cutoffDifference.toFixed(3)} points surplus`
                  : `${result.cutoffDifference.toFixed(3)} points below top cutoff`}
              </span>
            </div>
          </div>

          {/* Decision Narrative */}
          <div className="bg-indigo-50/70 rounded-xl p-3 border border-indigo-100/80 space-y-1">
            <div className="flex items-center space-x-1.5 text-indigo-950 font-bold text-xs">
              <Award className="w-4 h-4 text-[#4F46E5]" />
              <span>Multi-Attribute Recommendation Rationale</span>
            </div>
            <p className="text-slate-700 text-[11px] leading-relaxed">
              {shapExplanation.explanationText}
            </p>
          </div>

          {/* SHAP Feature Contribution Waterfall / Bars */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-800 text-xs flex items-center space-x-1">
                <TrendingUp className="w-3.5 h-3.5 text-teal-600" />
                <span>Feature Importance Weights (SHAP Attributions)</span>
              </span>
              <span className="text-[10px] text-slate-400">Relative Weight</span>
            </div>

            <div className="space-y-2 pt-1">
              {features.map(([featureName, weight]) => {
                const percentage = Math.min(100, Math.round(weight * 220));

                return (
                  <div key={featureName} className="space-y-0.5">
                    <div className="flex justify-between text-[10px] font-semibold text-slate-700">
                      <span>{featureName}</span>
                      <span className="text-teal-700 font-bold">+{weight.toFixed(3)}</span>
                    </div>

                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden flex">
                      <div
                        className="bg-gradient-to-r from-teal-400 to-[#4F46E5] h-full rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Positive Match Drivers */}
          {shapExplanation.positiveDrivers.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-slate-100">
              <h4 className="text-[11px] font-bold text-slate-800 flex items-center space-x-1">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                <span>Key Positive Predictors</span>
              </h4>
              <ul className="space-y-1">
                {shapExplanation.positiveDrivers.map((driver, i) => (
                  <li key={i} className="text-[11px] text-slate-600 flex items-start space-x-1.5">
                    <span className="text-emerald-500 font-bold">&bull;</span>
                    <span>{driver}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Academic Guidance */}
          {shapExplanation.potentialGaps.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-slate-100">
              <h4 className="text-[11px] font-bold text-amber-800 flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Admission Guidance & Competition</span>
              </h4>
              <ul className="space-y-1">
                {shapExplanation.potentialGaps.map((gap, i) => (
                  <li key={i} className="text-[11px] text-slate-600 flex items-start space-x-1.5">
                    <span className="text-amber-500 font-bold">&bull;</span>
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Close button */}
        <div className="p-3.5 border-t border-slate-100 bg-slate-50 shrink-0">
          <button
            onClick={onClose}
            className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-colors cursor-pointer"
          >
            Done Reviewing Explanation
          </button>
        </div>
      </div>
    </div>
  );
};
