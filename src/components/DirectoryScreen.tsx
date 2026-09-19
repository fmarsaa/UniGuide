import React, { useState, useMemo } from 'react';
import { ProgrammeInfo } from '../types';
import { Search, Filter, Bookmark, BookmarkCheck, ChevronRight, BookOpen } from 'lucide-react';

interface DirectoryScreenProps {
  programmes: ProgrammeInfo[];
  savedIds: string[];
  onToggleSave: (id: string) => void;
  onOpenDetails: (programme: ProgrammeInfo) => void;
}

export const DirectoryScreen: React.FC<DirectoryScreenProps> = ({
  programmes,
  savedIds,
  onToggleSave,
  onOpenDetails,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const categories = useMemo(() => {
    const cats = Array.from(new Set(programmes.map((p) => p.category)));
    return ['All', ...cats];
  }, [programmes]);

  const filtered = useMemo(() => {
    return programmes.filter((p) => {
      const matchCat = selectedCategory === 'All' || p.category === selectedCategory;
      const matchSearch =
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.universities.some((u) => u.name.toLowerCase().includes(searchTerm.toLowerCase()));
      return matchCat && matchSearch;
    });
  }, [programmes, selectedCategory, searchTerm]);

  return (
    <div className="flex-1 overflow-y-auto bg-[#F8FAFC] p-4 space-y-3">
      {/* Search & Header */}
      <div>
        <h2 className="text-sm font-bold text-slate-900 flex items-center space-x-1.5">
          <BookOpen className="w-4 h-4 text-[#4F46E5]" />
          <span>Kenyan University Degree Catalog</span>
        </h2>
        <p className="text-[10px] text-slate-500">
          Official KUCCPS degree programmes and admission requirements
        </p>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search degree, code, or university..."
          className="w-full pl-8 pr-3 py-2 text-xs bg-white rounded-xl border border-slate-200 shadow-2xs focus:outline-none focus:ring-2 focus:ring-[#4F46E5]"
        />
      </div>

      {/* Category Pills Slider */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 no-scrollbar text-[10px] font-semibold">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1 rounded-full whitespace-nowrap transition-all cursor-pointer ${
              selectedCategory === cat
                ? 'bg-[#4F46E5] text-white shadow-xs'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between text-[10px] text-slate-500 px-1">
        <span>Showing {filtered.length} programmes</span>
        {selectedCategory !== 'All' && <span>Filtered by: {selectedCategory}</span>}
      </div>

      {/* Programme Cards List */}
      <div className="space-y-2">
        {filtered.map((prog) => {
          const isSaved = savedIds.includes(prog.id);
          const primaryUni = prog.universities[0];

          return (
            <div
              key={prog.id}
              className="bg-white rounded-xl p-3 border border-slate-200/80 shadow-xs hover:border-slate-300 transition-all space-y-2"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-0.5 flex-1 min-w-0">
                  <div className="flex items-center space-x-1.5">
                    <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700">
                      {prog.code}
                    </span>
                    <span className="text-[9px] text-slate-400 font-medium">
                      {prog.category}
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-slate-900 leading-snug truncate">
                    {prog.name}
                  </h3>
                  <p className="text-[10px] text-slate-500">
                    Min Mean: <strong className="text-slate-700">{prog.admissionRequirements.minimumMeanGrade}</strong> &bull; {prog.durationYears} yrs
                  </p>
                </div>

                <button
                  onClick={() => onToggleSave(prog.id)}
                  className={`p-1.5 rounded-lg transition-colors cursor-pointer shrink-0 ${
                    isSaved ? 'text-amber-500 bg-amber-50' : 'text-slate-400 hover:text-slate-600'
                  }`}
                >
                  {isSaved ? <BookmarkCheck className="w-4 h-4 fill-amber-500" /> : <Bookmark className="w-4 h-4" />}
                </button>
              </div>

              {/* Bottom Row: University & Details CTA */}
              <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[10px] text-slate-600 truncate max-w-[190px]">
                  {primaryUni?.name || 'Accredited Universities'}
                </span>

                <button
                  onClick={() => onOpenDetails(prog)}
                  className="text-[10px] font-bold text-[#4F46E5] hover:underline flex items-center space-x-0.5 cursor-pointer"
                >
                  <span>Details</span>
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
