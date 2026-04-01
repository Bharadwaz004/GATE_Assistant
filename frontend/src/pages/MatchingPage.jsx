import React, { useEffect } from 'react';
import {
  Users, Loader2, BookOpen, GraduationCap, Sparkles, UserCheck,
} from 'lucide-react';
import clsx from 'clsx';
import useStore from '../store/useStore';

function MatchCard({ match, index }) {
  const scorePercent = Math.round(match.similarity_score * 100);

  // Color gradient based on score
  const scoreColor =
    scorePercent >= 80 ? 'text-success-600 bg-success-500/10' :
    scorePercent >= 60 ? 'text-brand-600 bg-brand-100' :
    'text-surface-600 bg-surface-100';

  return (
    <div
      className="glass-card-hover p-5 animate-slide-up"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white text-lg font-bold flex-shrink-0 shadow-md">
          {match.full_name.charAt(0).toUpperCase()}
        </div>

        <div className="flex-1 min-w-0">
          {/* Name + match score */}
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold text-surface-900 truncate">{match.full_name}</h3>
            <span className={clsx('text-sm font-bold px-2.5 py-1 rounded-lg', scoreColor)}>
              {scorePercent}%
            </span>
          </div>

          {/* Branch + prep type */}
          <div className="flex items-center gap-3 mt-1.5 text-sm text-surface-500">
            <span className="flex items-center gap-1">
              <GraduationCap className="w-3.5 h-3.5" /> {match.branch}
            </span>
            <span className="flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5" />
              {match.prep_type === 'coaching' ? 'Coaching' : 'Self Study'}
            </span>
          </div>

          {/* Subjects */}
          <div className="flex flex-wrap gap-1.5 mt-3">
            {match.subjects.map((subj) => (
              <span
                key={subj}
                className={clsx(
                  'text-xs px-2 py-0.5 rounded-full font-medium',
                  match.common_subjects.includes(subj)
                    ? 'bg-brand-100 text-brand-700 border border-brand-200'
                    : 'bg-surface-100 text-surface-500'
                )}
              >
                {subj}
              </span>
            ))}
          </div>

          {/* Common subjects highlight */}
          {match.common_subjects.length > 0 && (
            <div className="flex items-center gap-1.5 mt-3 text-xs text-brand-600">
              <Sparkles className="w-3.5 h-3.5" />
              <span className="font-medium">
                {match.common_subjects.length} common subject{match.common_subjects.length > 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function MatchingPage() {
  const { matches, fetchMatches, matchLoading } = useStore();

  useEffect(() => {
    fetchMatches(20).catch(() => {});
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-surface-900">Study Partners</h1>
          <p className="text-surface-500 mt-1">
            Matched based on branch, subjects, study schedule, and progress
          </p>
        </div>
        <button
          onClick={() => fetchMatches(20)}
          disabled={matchLoading}
          className="btn-outline"
        >
          {matchLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <><UserCheck className="w-4 h-4" /> Refresh Matches</>
          )}
        </button>
      </div>

      {/* How matching works */}
      <div className="glass-card p-5 bg-gradient-to-r from-brand-50/60 to-transparent border-brand-200/40">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-brand-500 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-surface-900 text-sm">AI-Powered Matching</h3>
            <p className="text-sm text-surface-500 mt-0.5">
              We use sentence-transformer embeddings to analyze your profile — branch, subjects,
              study timings, and preparation style — and compute cosine similarity scores to find
              the most compatible study partners for you.
            </p>
          </div>
        </div>
      </div>

      {/* Loading */}
      {matchLoading && !matches && (
        <div className="glass-card p-16 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-brand-500 mx-auto mb-4" />
          <p className="text-surface-500">Finding your ideal study partners...</p>
        </div>
      )}

      {/* Results */}
      {matches?.matches?.length > 0 ? (
        <div>
          <p className="text-sm text-surface-500 mb-4">
            Found <span className="font-semibold text-surface-700">{matches.total_found}</span> potential partners
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {matches.matches.map((match, i) => (
              <MatchCard key={match.user_id} match={match} index={i} />
            ))}
          </div>
        </div>
      ) : !matchLoading ? (
        <div className="glass-card p-16 text-center">
          <Users className="w-16 h-16 text-surface-200 mx-auto mb-4" />
          <h3 className="font-display text-xl text-surface-700 mb-2">No matches found yet</h3>
          <p className="text-surface-400 max-w-md mx-auto">
            As more aspirants join and complete their profiles, you'll start seeing compatible
            study partners here. Check back soon!
          </p>
        </div>
      ) : null}
    </div>
  );
}
